import base64
import hashlib
import json
import re
import subprocess
import tempfile
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from loguru import logger

# ナビ用画像（ページ送り矢印など）のファイル名。本体画像ではないので除外する。
KNOWN_NAV_NAMES = {"left.png", "right.png"}

# HTML/XHTML に埋め込まれた data:image;base64 を拾う（EPUB ページの本体画像など）。
_DATA_IMG_RE = re.compile(r"data:(image/[\w.+-]+);base64,([A-Za-z0-9+/=\s]+)")


def extract_embedded_image(data: bytes) -> bytes | None:
    """HTML/XML テキスト中の data:image base64 のうち、最大のものをデコードして返す。

    EPUB ビューアのように、本体画像が XHTML 内へ base64 で埋め込まれている場合に使う。
    見つからなければ None。
    """
    text = data.decode("utf-8", "replace")
    best: bytes | None = None
    for _mime, b64 in _DATA_IMG_RE.findall(text):
        cleaned = "".join(b64.split())
        try:
            raw = base64.b64decode(cleaned)
        except (ValueError, TypeError):
            continue
        if best is None or len(raw) > len(best):
            best = raw
    return best


def sniff_media(head: bytes) -> str:
    """先頭バイト（マジックナンバー）から画像フォーマットを推定する。"""
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return "unknown"


def is_nav_image(src: str) -> bool:
    """src の basename が既知のナビ画像名なら True。"""
    if not src:
        return False
    path = src.split("?", 1)[0]
    basename = path.rsplit("/", 1)[-1]
    return basename in KNOWN_NAV_NAMES


def sniffed_ext(data: bytes) -> str:
    """バイト列から拡張子を決める。判別不能なら 'bin'。"""
    ext = sniff_media(data[:16])
    return ext if ext != "unknown" else "bin"


def hashed_filename(data: bytes, ext: str) -> str:
    """内容の sha256 先頭16桁＋拡張子のファイル名を作る（同一内容→同一名で重複排除）。"""
    digest = hashlib.sha256(data).hexdigest()[:16]
    return f"{digest}.{ext}"


def parse_meta(raw: str) -> list[dict]:
    """抽出 JS が返した候補メタ JSON をパースする。壊れていれば空リスト。"""
    raw = raw.strip()
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


class SafariError(Exception):
    """Safari への JS 注入（osascript）が失敗したことを表す。"""


# on run argv: item 1 = JS 文字列, item 2 = URL 部分一致（任意）。
# JS を argv で渡すことで、引用符・改行のエスケープ問題を回避する。
_APPLESCRIPT = """
on run argv
	set jsCode to item 1 of argv
	set urlSubstr to ""
	if (count of argv) >= 2 then set urlSubstr to item 2 of argv
	tell application "Safari"
		if urlSubstr is "" then
			return (do JavaScript jsCode in front document)
		else
			repeat with w in windows
				repeat with t in tabs of w
					if (URL of t) contains urlSubstr then
						return (do JavaScript jsCode in t)
					end if
				end repeat
			end repeat
			error "no tab matched url substring: " & urlSubstr
		end if
	end tell
end run
"""


# 開いている全タブの URL を改行区切りで返す（対象タブ特定の補助）。
_LIST_TABS_APPLESCRIPT = """
tell application "Safari"
	set out to ""
	repeat with w in windows
		repeat with t in tabs of w
			set out to out & (URL of t) & linefeed
		end repeat
	end repeat
	return out
end tell
"""


@lru_cache(maxsize=None)
def _script_path(script: str) -> str:
    """AppleScript 本体を一時ファイルに書き出し、そのパスを返す（内容ごとにキャッシュ）。"""
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".applescript", delete=False, encoding="utf-8"
    )
    f.write(script)
    f.close()
    return f.name


def list_safari_tabs() -> list[str]:
    """開いている Safari の全タブ URL を返す。"""
    proc = subprocess.run(
        ["osascript", _script_path(_LIST_TABS_APPLESCRIPT)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SafariError(friendly_error(proc.stderr.strip()))
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


def friendly_error(stderr: str) -> str:
    """osascript の stderr を、対処法つきの分かりやすい文言に変換する。"""
    low = stderr.lower()
    if "not allowed" in low or "apple events" in low:
        return (
            "Safari で JS 実行が許可されていません。"
            "「開発」メニュー →「Apple Events からの JavaScript を許可」を ON にしてください。\n"
            f"元エラー: {stderr}"
        )
    if "-1743" in stderr or "not permitted" in low or "not authoriz" in low:
        return (
            "オートメーションの許可がありません。"
            "設定 → プライバシーとセキュリティ → オートメーション で、"
            "実行元アプリ（ターミナル等）から Safari の操作を許可してください。\n"
            f"元エラー: {stderr}"
        )
    if "no tab matched" in low:
        return (
            "対象タブが見つかりませんでした。ビューアを Safari で開くか、"
            "--url-substr で対象タブの URL 部分一致を指定してください。\n"
            f"元エラー: {stderr}"
        )
    return stderr


def run_js_in_safari(js: str, url_substr: str | None = None) -> str:
    """Safari の対象タブで JS を実行し、戻り値（文字列）を返す。

    url_substr が指定されればその URL 部分一致タブ、無ければ最前面 document で実行する。
    失敗時は friendly_error で整形して SafariError を送出する。
    """
    args = ["osascript", _script_path(_APPLESCRIPT), js]
    if url_substr:
        args.append(url_substr)
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SafariError(friendly_error(proc.stderr.strip()))
    return proc.stdout.rstrip("\n")


# 候補画像を決定的な順序で収集する共有ロジック。文書全体＋同一オリジン iframe を
# 再帰走査し、img / background-image / blob: iframe を順に並べる。
# META_JS と build_fetch_js が同一の順序で index を採番できるよう、両者で共用する。
_COLLECT_FN = r"""
  function collect() {
    const items = [];
    const seen = {};
    function scan(doc) {
      for (const img of doc.querySelectorAll('img')) {
        const s = img.currentSrc || img.src;
        if (!s || seen[s]) continue;
        seen[s] = 1;
        items.push({kind: 'img', el: img, src: s});
      }
      for (const el of doc.querySelectorAll('*')) {
        const bg = getComputedStyle(el).backgroundImage;
        if (bg && bg !== 'none' && bg.indexOf('url(') !== -1) {
          const m = bg.match(/url\((['"]?)(.*?)\1\)/);
          const u = m ? m[2] : '';
          if (u && !seen[u]) { seen[u] = 1; items.push({kind: 'bg', el: el, src: u}); }
        }
      }
      for (const f of doc.querySelectorAll('iframe')) {
        const s = f.src || '';
        if (s.indexOf('blob:') === 0 && !seen[s]) {
          seen[s] = 1;
          items.push({kind: 'iframe', el: f, src: s});
        }
        let cd = null;
        try { cd = f.contentDocument; } catch (e) { cd = null; }
        if (cd) scan(cd);
      }
    }
    scan(document);
    return items;
  }
  function dimW(it) { return it.kind === 'img' ? (it.el.naturalWidth || 0) : 0; }
  function dimH(it) { return it.kind === 'img' ? (it.el.naturalHeight || 0) : 0; }
"""

# 収集した候補のメタ情報（index/kind/w/h/src）を JSON 文字列で返す。
META_JS = (
    r"""
(function () {
"""
    + _COLLECT_FN
    + r"""
  const items = collect();
  const meta = items.map((it, i) => ({index: i, kind: it.kind, w: dimW(it), h: dimH(it), src: it.src}));
  return JSON.stringify(meta);
})();
"""
)


def build_fetch_js(index: int) -> str:
    """指定 index の画像を base64 で返す JS を組み立てる（走査順は META_JS と一致）。

    do JavaScript は Promise を待たないため、blob:/http は同期 XHR +
    overrideMimeType('text/plain; charset=x-user-defined') でバイナリを読み取る。
    """
    return (
        r"""
(function () {
  const TARGET = %d;
  function readSync(url) {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', url, false);
    try { xhr.overrideMimeType('text/plain; charset=x-user-defined'); } catch (e) {}
    xhr.send();
    if (xhr.status && xhr.status !== 200 && xhr.status !== 0) throw new Error('status ' + xhr.status);
    const t = xhr.responseText;
    let binary = '';
    for (let i = 0; i < t.length; i++) binary += String.fromCharCode(t.charCodeAt(i) & 0xff);
    return btoa(binary);
  }
""" % index
        + _COLLECT_FN
        + r"""
  const items = collect();
  if (TARGET < 0 || TARGET >= items.length) return '';
  const it = items[TARGET];
  if (it.src.indexOf('data:') === 0) return (it.src.split(',')[1] || '');
  return readSync(it.src);
})();
"""
    )


# 診断用: トップ文書＋同一オリジン iframe を再帰走査し、フレーム別の
# img/canvas/bg 一覧と iframe の同一オリジン可否を JSON で返す。
# クロスオリジン iframe は contentDocument 参照が例外になるため sameOrigin:false。
INVENTORY_JS = r"""
(function () {
  // blob:/http/data の中身を同期取得し、先頭バイト（16進）とサイズを返す。
  // マジックナンバーで実体（jpeg/png/html 等）を識別するための診断用。
  function probeHead(url) {
    if (url.indexOf('data:') === 0) {
      return {bytes: url.length, head: 'data-uri:' + url.slice(0, 32)};
    }
    try {
      const xhr = new XMLHttpRequest();
      xhr.open('GET', url, false);
      try { xhr.overrideMimeType('text/plain; charset=x-user-defined'); } catch (e) {}
      xhr.send();
      const t = xhr.responseText;
      const n = Math.min(t.length, 16);
      let hex = '';
      for (let i = 0; i < n; i++) hex += (t.charCodeAt(i) & 0xff).toString(16).padStart(2, '0');
      return {bytes: t.length, head: hex};
    } catch (e) { return {error: String(e)}; }
  }
  function scan(doc, path, results) {
    const out = {path: path, imgs: [], canvases: [], bgs: [], iframes: []};
    try {
      for (const img of doc.querySelectorAll('img')) {
        const s = img.currentSrc || img.src || '';
        const rec = {w: img.naturalWidth || 0, h: img.naturalHeight || 0, src: s.slice(0, 200)};
        if (s.indexOf('blob:') === 0 || s.indexOf('data:') === 0) rec.probe = probeHead(s);
        out.imgs.push(rec);
      }
      for (const c of doc.querySelectorAll('canvas')) out.canvases.push({w: c.width, h: c.height});
      for (const el of doc.querySelectorAll('*')) {
        const bg = getComputedStyle(el).backgroundImage;
        if (bg && bg !== 'none' && bg.indexOf('url(') !== -1) {
          const m = bg.match(/url\((['"]?)(.*?)\1\)/);
          if (m) out.bgs.push(m[2].slice(0, 200));
        }
      }
    } catch (e) { out.error = String(e); }
    const children = [];
    const ifr = doc.querySelectorAll('iframe');
    for (let i = 0; i < ifr.length; i++) {
      const s = ifr[i].src || '';
      const info = {index: i, src: s.slice(0, 200), sameOrigin: false};
      if (s.indexOf('blob:') === 0 || s.indexOf('data:') === 0) info.probe = probeHead(s);
      let cd = null;
      try { cd = ifr[i].contentDocument; if (cd) info.sameOrigin = true; } catch (e) { info.sameOrigin = false; }
      // 同一オリジンなら中身の HTML 冒頭も見る（画像 document か HTML ラッパかの判別用）。
      if (cd) {
        try { info.innerHTML = (cd.documentElement ? cd.documentElement.outerHTML : '').slice(0, 300); } catch (e) {}
      }
      out.iframes.push(info);
      if (cd) children.push({doc: cd, path: path + '>iframe[' + i + ']'});
    }
    results.push(out);
    for (const ch of children) scan(ch.doc, ch.path, results);
  }
  const results = [];
  scan(document, 'top', results);
  return JSON.stringify(results);
})();
"""


def _add_log_sink(output_dir: Path) -> None:
    """出力先に grab.log を作り、以降のログをファイルにも残す。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.add(output_dir / "grab.log", level="DEBUG", encoding="utf-8")


def inventory(url_substr: str | None, output_dir: Path) -> Path:
    """全タブ URL と、対象タブのフレーム別 DOM 一覧を書き出す診断モード。"""
    _add_log_sink(output_dir)
    tabs = list_safari_tabs()
    logger.info(f"Safari タブ {len(tabs)} 個:")
    for i, u in enumerate(tabs):
        logger.info(f"  [{i}] {u}")

    raw = run_js_in_safari(INVENTORY_JS, url_substr)
    frames: list[dict] = json.loads(raw) if raw.strip() else []

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"inventory-{datetime.now():%Y%m%d-%H%M%S}.json"
    path.write_text(json.dumps(frames, ensure_ascii=False, indent=2), encoding="utf-8")

    for fr in frames:
        imgs = fr.get("imgs", [])
        dims = sorted({f"{i['w']}x{i['h']}" for i in imgs})
        logger.info(
            f"[FRAME {fr.get('path')}] img={len(imgs)} dims={dims} "
            f"canvas={len(fr.get('canvases', []))} bg={len(fr.get('bgs', []))} "
            f"iframes={len(fr.get('iframes', []))}"
        )
        for f2 in fr.get("iframes", []):
            logger.info(
                f"    iframe[{f2['index']}] sameOrigin={f2['sameOrigin']} "
                f"probe={f2.get('probe')} src={f2['src']}"
            )
        for im in imgs:
            if im.get("probe"):
                logger.info(
                    f"    img {im['w']}x{im['h']} probe={im['probe']} src={im['src']}"
                )
    logger.info(f"inventory -> {path}")
    return path


def grab(url_substr: str | None, output_dir: Path, min_bytes: int) -> list[Path]:
    """Safari の対象タブから候補画像を抜き出し、指定ディレクトリ直下に保存する。

    ファイル名は内容の sha256 先頭16桁とするため、同一内容が既にあれば SKIP する。
    """
    dest = output_dir
    _add_log_sink(dest)

    raw = run_js_in_safari(META_JS, url_substr)
    meta = parse_meta(raw)
    logger.info(f"候補 {len(meta)} 件を検出")

    saved: list[tuple[Path, int]] = []
    for m in meta:
        src = m.get("src", "")
        if is_nav_image(src):
            logger.info(f"[SKIP] ナビ画像 idx={m['index']} src={src}")
            continue
        try:
            b64 = run_js_in_safari(build_fetch_js(int(m["index"])), url_substr)
        except SafariError as e:
            logger.warning(f"[SKIP] 取得失敗 idx={m['index']}: {e}")
            continue
        if not b64:
            continue
        try:
            data = base64.b64decode(b64)
        except (ValueError, TypeError) as e:
            logger.warning(f"[SKIP] base64 デコード失敗 idx={m['index']}: {e}")
            continue
        ext = sniffed_ext(data)
        if ext == "bin":
            # 画像バイトでない（blob: iframe が XHTML/SVG ラッパ等）→ 埋め込み data:image を探す。
            embedded = extract_embedded_image(data)
            if embedded is None:
                logger.info(
                    f"[SKIP] 非画像/埋め込み無し idx={m['index']} kind={m['kind']} "
                    f"bytes={len(data)} head={data[:60]!r}"
                )
                continue
            logger.info(
                f"[UNWRAP] idx={m['index']} XHTML {len(data)}B から"
                f"埋め込み画像 {len(embedded)}B を抽出"
            )
            data = embedded
            ext = sniffed_ext(data)
            if ext == "bin":
                logger.info(f"[SKIP] 埋め込みデコード不可 idx={m['index']}")
                continue
        if len(data) < min_bytes:
            logger.info(
                f"[SKIP] 小さすぎ idx={m['index']} ({len(data)}B < {min_bytes}B)"
            )
            continue
        path = dest / hashed_filename(data, ext)
        if path.exists():
            logger.info(f"[SKIP] 既存 idx={m['index']} -> {path.name}")
            continue
        path.write_bytes(data)
        saved.append((path, len(data)))
        logger.info(f"[SAVE] {path} ({len(data)}B) {m.get('w')}x{m.get('h')}")

    if not saved:
        logger.warning("保存できた画像はありませんでした。")
    return [p for p, _ in saved]


if __name__ == "__main__":
    import argparse

    default_out = Path.home() / "Downloads" / "musabi" / "grab"

    parser = argparse.ArgumentParser(
        description=(
            "実 Safari の対象タブから、表示中ビューアの読み込み済み全スライドの画像を抜き出す。"
            "事前に Safari「開発」→「Apple Events からの JavaScript を許可」を ON にすること。"
        ),
    )
    parser.add_argument(
        "--url-substr",
        default=None,
        help="対象タブの URL 部分一致（省略時は最前面タブ）",
    )
    parser.add_argument(
        "--output",
        default=str(default_out),
        help="保存先ディレクトリ（直下に内容ハッシュ名で保存。同一画像は SKIP）",
    )
    parser.add_argument(
        "--min-bytes",
        type=int,
        default=100_000,
        help="このバイト数未満の画像は除外（ナビ/空canvas/サムネ対策）",
    )
    parser.add_argument(
        "--inventory",
        action="store_true",
        help="診断モード: 抜き出さず、全タブ URL とフレーム別 DOM 一覧を出力する",
    )
    args = parser.parse_args()

    try:
        if args.inventory:
            inventory(args.url_substr, Path(args.output))
        else:
            grab(args.url_substr, Path(args.output), args.min_bytes)
    except SafariError as e:
        logger.error(str(e))
        raise SystemExit(1)
