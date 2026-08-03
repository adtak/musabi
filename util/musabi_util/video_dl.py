"""ID リストを元に、投稿ページの動画 API から HLS を取得して mp4 で保存する。

認証は API 層だけに掛かっており、m3u8 を配信する CDN 側は素通しになっている。
そのため API から m3u8 の URL さえ取れれば、ダウンロード自体は追加のヘッダ無しで動く。

一時名 `<id>.tmp.<ext>` で落とし、尺の検証を通ったものだけを `<id>.<ext>` へ
リネームする。これにより「最終ファイルが存在する = 検証済みで完成している」が
常に成り立ち、中断した半端なファイルを完成扱いする事故が起きない。
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import yt_dlp
from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm

API_PATH = "/api/v2/posts/{post_id}/videos"

# API 呼び出しの間隔（秒）。動画本体のダウンロードで自然に間隔は空くが、
# スキップが連続した場合などに備えて明示的に待つ。
DEFAULT_INTERVAL_S = 60.0

# 実測の尺と API 申告の尺の許容差（秒）。HLS は断片単位なので端数がずれる。
DEFAULT_TOLERANCE_S = 2.0

_ENV_KEYS = ("VIDEO_API_BASE", "VIDEO_API_TOKEN", "VIDEO_API_CLIENT_HEADER")


class VideoDlError(Exception):
    """1 件の処理が失敗したことを表す（他の ID の処理は継続する）。"""


class AuthError(VideoDlError):
    """認証・クライアント判定で弾かれた（以降も全て失敗するので処理を打ち切る）。"""


@dataclass(frozen=True)
class ApiConfig:
    """API を叩くのに必要な設定。すべて .env から読む。"""

    base: str
    token: str
    client_header: str

    @classmethod
    def from_env(cls) -> "ApiConfig":
        load_dotenv()
        values = {k: os.getenv(k, "").strip() for k in _ENV_KEYS}
        missing = [k for k, v in values.items() if not v]
        if missing:
            raise VideoDlError(
                f".env に {', '.join(missing)} が設定されていません。"
                ".env.sample を参照してください。"
            )
        return cls(
            base=values["VIDEO_API_BASE"].rstrip("/"),
            token=values["VIDEO_API_TOKEN"],
            client_header=values["VIDEO_API_CLIENT_HEADER"],
        )


@dataclass(frozen=True)
class Video:
    """API が返す動画候補のうち 1 本分。"""

    url: str
    width: int
    height: int
    duration_ms: int
    resolution: str


def parse_ids(text: str) -> list[str]:
    """1 行 1 ID のテキストから ID を取り出す。

    `#` 以降はコメントとして落とし、空行と重複は無視する。落とし終えた ID を
    コメントアウトしてメモを残す運用を想定している。
    """
    ids: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        body = line.split("#", 1)[0].strip()
        if not body or body in seen:
            continue
        seen.add(body)
        ids.append(body)
    return ids


def pick_best(payload: dict) -> Video:
    """`main` の中から最も解像度の高いものを選ぶ。

    `trial`（数十秒のサンプル）は常に無視する。`resolution` は "sd"/"fhd" という
    文字列なので順序比較に使えない。必ず width/height の数値で比較する。
    """
    entries = payload.get("main") or []
    if not isinstance(entries, list) or not entries:
        raise VideoDlError("`main` が空です（未購入、または体験版のみ公開の可能性）")

    best = max(
        entries,
        key=lambda v: (int(v.get("width") or 0), int(v.get("height") or 0)),
    )
    url = best.get("url")
    if not url:
        raise VideoDlError("選択した動画に url がありません")

    return Video(
        url=url,
        width=int(best.get("width") or 0),
        height=int(best.get("height") or 0),
        duration_ms=int(best.get("duration_ms") or 0),
        resolution=str(best.get("resolution") or "?"),
    )


def duration_matches(
    actual_s: float, expected_ms: int, tol_s: float = DEFAULT_TOLERANCE_S
) -> bool:
    """実測の尺が API 申告の尺と一致するか。申告が無い場合は検証しない。"""
    if expected_ms <= 0:
        return True
    return abs(actual_s - expected_ms / 1000.0) <= tol_s


def auth_error_message(status: int) -> str:
    """401/403 に対処法を添える。半年後の自分が原因にたどり着けるように。"""
    if status == 403:
        return (
            "HTTP 403: クライアント判定で弾かれました。\n"
            "VIDEO_API_CLIENT_HEADER の値が古くなった可能性があります。"
            "ブラウザの Web インスペクタで、リソースを 'google-ga-data' で"
            "全文検索し、JS バンドル内の最新の値に .env を更新してください。"
        )
    return (
        f"HTTP {status}: 認証に失敗しました。\n"
        "VIDEO_API_TOKEN を取り直してください。ログイン済みブラウザで動画 API の"
        "リクエストを開き、Authorization ヘッダの 'Token token=' 以降の値を使います。"
    )


def fetch_meta(cfg: ApiConfig, post_id: str) -> dict:
    """動画 API を叩いて JSON を返す。"""
    url = cfg.base + API_PATH.format(post_id=post_id)
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Token token={cfg.token}",
            "google-ga-data": cfg.client_header,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            raw = res.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise AuthError(auth_error_message(e.code)) from e
        raise VideoDlError(f"API がエラーを返しました: HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise VideoDlError(f"API に接続できません: {e.reason}") from e

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        raise VideoDlError(
            f"API のレスポンスが JSON ではありません: {raw[:120]!r}"
        ) from e
    if not isinstance(payload, dict):
        raise VideoDlError(f"想定外のレスポンス形式です: {type(payload).__name__}")
    return payload


def existing_output(output: Path, post_id: str) -> Path | None:
    """検証済みの最終ファイルが既にあれば返す（一時ファイルは無視する）。"""
    for path in sorted(output.glob(f"{post_id}.*")):
        if ".tmp." in path.name or path.suffix == ".part":
            continue
        return path
    return None


class DownloadProgress:
    """yt-dlp の progress_hooks を tqdm のバーに橋渡しする。

    HLS は総バイト数が事前に分からないことが多い一方、断片数は取れる。
    そこで断片数が分かる場合はそちらを進捗の単位にし、分からない場合だけ
    バイト数にフォールバックする。
    """

    def __init__(self, desc: str) -> None:
        self.desc = desc
        self.bar: tqdm | None = None
        self.by_fragment = False

    def hook(self, status: dict) -> None:
        state = status.get("status")
        if state == "downloading":
            self._update(status)
        elif state in ("finished", "error"):
            self.close()

    def _update(self, status: dict) -> None:
        if self.bar is None:
            self.bar = self._open(status)
        current = (
            status.get("fragment_index")
            if self.by_fragment
            else status.get("downloaded_bytes")
        )
        if current is None:
            return
        # 差分ではなく絶対値で置く。フックの取りこぼしがあってもずれない。
        self.bar.n = current
        self.bar.refresh()

    def _open(self, status: dict) -> tqdm:
        frag_total = status.get("fragment_count")
        self.by_fragment = bool(frag_total)
        common = {
            "desc": self.desc,
            "leave": False,
            # 非 tty（ログへのリダイレクト等）ではバーを出さない。
            "disable": not sys.stderr.isatty(),
        }
        if self.by_fragment:
            return tqdm(total=frag_total, unit="frag", **common)
        return tqdm(
            total=status.get("total_bytes") or status.get("total_bytes_estimate"),
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            **common,
        )

    def close(self) -> None:
        if self.bar is None:
            return
        if self.bar.total:
            self.bar.n = self.bar.total
            self.bar.refresh()
        self.bar.close()
        self.bar = None


def download(url: str, output: Path, post_id: str) -> Path:
    """m3u8 を一時名で落とし、生成されたファイルのパスを返す。"""
    stem = f"{post_id}.tmp"
    for stale in output.glob(f"{stem}.*"):
        stale.unlink()

    progress = DownloadProgress(post_id)
    opts = {
        "outtmpl": str(output / f"{stem}.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        # yt-dlp 自身の進捗表示は止め、tqdm に一本化する。
        "noprogress": True,
        "progress_hooks": [progress.hook],
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            code = ydl.download([url])
    finally:
        progress.close()
    if code:
        raise VideoDlError(f"yt-dlp が失敗しました (code={code})")

    produced = [p for p in output.glob(f"{stem}.*") if p.suffix != ".part"]
    if len(produced) != 1:
        raise VideoDlError(
            f"出力ファイルを特定できません: {[p.name for p in produced]}"
        )
    return produced[0]


def probe_duration(path: Path) -> float | None:
    """ffprobe で尺（秒）を取る。ffprobe が無い・読めない場合は None。"""
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                str(path),
            ],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None
    if proc.returncode != 0:
        return None
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return None


def _add_log_sink(output: Path) -> None:
    """出力先に video_dl.log を作り、以降のログをファイルにも残す。"""
    output.mkdir(parents=True, exist_ok=True)
    logger.add(output / "video_dl.log", level="DEBUG", encoding="utf-8")


def run(
    cfg: ApiConfig,
    ids: list[str],
    output: Path,
    interval: float = DEFAULT_INTERVAL_S,
    tolerance: float = DEFAULT_TOLERANCE_S,
) -> list[str]:
    """ID を順に処理し、失敗した ID の一覧を返す。

    1 件失敗しても止めずに次へ進むが、認証エラーだけは以降も全て失敗するので
    その場で打ち切る。
    """
    _add_log_sink(output)
    logger.info(f"対象 {len(ids)} 件 -> {output}")

    saved = 0
    skipped = 0
    failed: list[str] = []
    called = False

    for post_id in ids:
        found = existing_output(output, post_id)
        if found:
            logger.info(f"[SKIP] {post_id} 既に {found.name} があります")
            skipped += 1
            continue

        # API を実際に叩く直前にだけ待つ（スキップ分では待たない）。
        if called and interval > 0:
            time.sleep(interval)
        called = True

        try:
            video = pick_best(fetch_meta(cfg, post_id))
            logger.info(
                f"[META] {post_id} {video.resolution} {video.width}x{video.height} "
                f"{video.duration_ms / 1000:.1f}s"
            )

            tmp = download(video.url, output, post_id)
            actual = probe_duration(tmp)
            if actual is None:
                logger.warning(
                    f"[WARN] {post_id} ffprobe で尺を確認できませんでした"
                    "（ffmpeg 未インストール？）。検証せず採用します"
                )
            elif not duration_matches(actual, video.duration_ms, tolerance):
                logger.error(
                    f"[FAIL] {post_id} 尺が一致しません "
                    f"(実測 {actual:.1f}s / 期待 {video.duration_ms / 1000:.1f}s)。"
                    f"確認用に {tmp.name} を残します"
                )
                failed.append(post_id)
                continue

            final = output / f"{post_id}{tmp.suffix}"
            tmp.rename(final)
            logger.info(f"[SAVE] {final} ({final.stat().st_size:,}B)")
            saved += 1

        except AuthError as e:
            logger.error(f"[ABORT] {post_id}: {e}")
            failed.append(post_id)
            logger.error("認証エラーのため処理を打ち切ります")
            break
        except VideoDlError as e:
            logger.error(f"[FAIL] {post_id}: {e}")
            failed.append(post_id)
        except Exception as e:  # yt-dlp / ffmpeg 由来の想定外エラー
            logger.error(f"[FAIL] {post_id}: {type(e).__name__}: {e}")
            failed.append(post_id)

    logger.info(f"成功 {saved} / スキップ {skipped} / 失敗 {len(failed)}")
    if failed:
        logger.error(f"失敗した ID: {', '.join(failed)}")
    return failed


if __name__ == "__main__":
    import argparse

    default_out = Path.home() / "Downloads" / "musabi" / "video"

    parser = argparse.ArgumentParser(
        description=(
            "ID リストを元に動画 API から HLS を取得し、mp4 で保存する。"
            "接続情報は .env（VIDEO_API_BASE / VIDEO_API_TOKEN / "
            "VIDEO_API_CLIENT_HEADER）から読む。"
        ),
    )
    parser.add_argument(
        "--ids",
        required=True,
        help="post ID を 1 行 1 件で並べたファイル（# 以降はコメント）",
    )
    parser.add_argument(
        "--output",
        default=str(default_out),
        help="保存先ディレクトリ（既に <id>.* がある ID はスキップ）",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL_S,
        help="API 呼び出しの間隔（秒）",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=DEFAULT_TOLERANCE_S,
        help="尺の検証で許容する誤差（秒）",
    )
    args = parser.parse_args()

    try:
        config = ApiConfig.from_env()
        id_list = parse_ids(Path(args.ids).read_text(encoding="utf-8"))
        if not id_list:
            logger.error(f"{args.ids} に処理対象の ID がありません")
            raise SystemExit(1)
        failures = run(
            config,
            id_list,
            Path(args.output),
            interval=args.interval,
            tolerance=args.tolerance,
        )
    except VideoDlError as err:
        logger.error(str(err))
        raise SystemExit(1)
    except FileNotFoundError as err:
        logger.error(f"ID ファイルが読めません: {err}")
        raise SystemExit(1)

    raise SystemExit(1 if failures else 0)
