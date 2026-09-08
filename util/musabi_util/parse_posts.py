"""投稿一覧ページの HTML から、video_dl の入力に使うメタ情報を抜き出す。

一覧では 1 投稿につき投稿ページへのリンクが 2 回出る（サムネイルとタイトル）。
そこで id ごとにマージし、常に初出の値を採用する。

タイトルは「`<img>` を含まない側のアンカーのテキスト」として取る。クラス名を
目印にする方が素直に見えるが、Tailwind のユーティリティクラスなのでサイト側の
微修正で簡単に変わる。サムネイル側のアンカーは必ず画像を含み、タイトル側は
含まないので、構造だけで確実に見分けられる。そのアンカー内にはタイトル以外の
テキストも入りうるため、最初の行だけをタイトルとして採用する。

日付はサムネイル画像のファイル名から取る。どの投稿の画像かは DOM の入れ子で
決め、URL のパスに入っている id とは突き合わせない。パスの形も、そこに現れる
id が投稿 id と一致するかも、当てにできないため。

出力は 1 行 1 件のタブ区切りで、そのまま ids.txt へ追記できる:

    uv run python -m musabi_util.parse_posts page.html >> ids.txt
    pbpaste | uv run python -m musabi_util.parse_posts >> ids.txt
"""

import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

from loguru import logger

DEFAULT_EXT = "mp4"

# 投稿ページへのリンク。一覧内の他のリンク（作者ページ等）はここで弾かれる。
_POST_HREF_RE = re.compile(r"^/posts/([\w-]+)$")

# サムネイル URL のファイル名に埋まっている投稿日。
#
# 見るのはファイル名だけで、ディレクトリ構成は一切見ない。ここは実際に
# post/thumbnail_image/... から post_image/square_image/... へ変わっており、
# さらにディレクトリ名の id は投稿 id と一致しないことがある。パスの形に
# 依存すると同じ壊れ方を繰り返す。
#
# どの投稿の画像かは URL ではなく DOM の入れ子で決める（_note_date を参照）。
_IMAGE_DATE_RE = re.compile(r"/image(\d{8})(?!\d)")

# ファイル名に使えない文字。macOS で問題になるのは / だけだが、他 OS や
# 外付けドライブへ移しても困らないよう Windows の禁則文字も落とす。
# `#` を含めるのは、ids.txt が `#` 以降をコメントとして扱うため。これを
# 残すと「C#入門」のようなタイトルで行が途中から切り捨てられる。
_UNSAFE_RE = re.compile(r'[/\\:*?"<>|#\x00-\x1f]')

# ファイル名全体（拡張子込み）の上限バイト数。APFS の上限は 255 バイトで、
# 日本語は 1 文字 3 バイトになるため、文字数ではなくバイト数で見る必要がある。
MAX_NAME_BYTES = 200


@dataclass(frozen=True)
class Post:
    """一覧から取れた 1 投稿分のメタ情報。取れなかった項目は None。"""

    id: str
    date: str | None
    title: str | None


@dataclass
class _Anchor:
    """走査中の `<a>` 1 つ分の状態。"""

    post_id: str | None
    has_img: bool = False
    chunks: list[str] = field(default_factory=list)


class _PostParser(HTMLParser):
    """一覧ページを 1 パスで走査し、id ごとに初出の日付とタイトルを拾う。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        # 文書中の初出順。出力の並びをこれで決める。
        self.order: list[str] = []
        self.dates: dict[str, str] = {}
        self.titles: dict[str, str] = {}
        self._stack: list[_Anchor] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a":
            self._open_anchor(values.get("href"))
        elif tag == "img":
            if self._stack:
                self._stack[-1].has_img = True
            self._note_date(values.get("src"))

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or not self._stack:
            return
        anchor = self._stack.pop()
        if anchor.post_id is None or anchor.has_img:
            return
        # アンカー内にはタイトル以外のテキストも入りうるので、最初の行だけを
        # タイトルとして扱う。後続の行を拾うと、無関係な文字列が繋がってしまう。
        text = "".join(anchor.chunks).strip()
        title = text.split("\n", 1)[0].strip()
        if title and anchor.post_id not in self.titles:
            self.titles[anchor.post_id] = title

    def handle_data(self, data: str) -> None:
        if self._stack:
            self._stack[-1].chunks.append(data)

    def _open_anchor(self, href: str | None) -> None:
        # 投稿ページ以外へのリンクも積む。そうしないと </a> の対応がずれる。
        match = _POST_HREF_RE.match(href or "")
        post_id = match.group(1) if match else None
        self._stack.append(_Anchor(post_id))
        if post_id and post_id not in self.order:
            self.order.append(post_id)

    def _note_date(self, src: str | None) -> None:
        """投稿ページへのアンカーの内側にある画像から、投稿日を拾う。

        どの投稿の画像かは入れ子で決まるので、URL の中の id とは突き合わせない。
        作者ページのアンカーの内側にあるアバター画像は、ここで自然に外れる。
        """
        post_id = self._enclosing_post_id()
        if post_id is None or post_id in self.dates:
            return
        match = _IMAGE_DATE_RE.search(src or "")
        if match:
            self.dates[post_id] = match.group(1)

    def _enclosing_post_id(self) -> str | None:
        for anchor in reversed(self._stack):
            if anchor.post_id is not None:
                return anchor.post_id
        return None


def parse_posts(html: str) -> list[Post]:
    """HTML から投稿を抜き出す。同一 id はマージし、初出順で返す。"""
    parser = _PostParser()
    parser.feed(html)
    parser.close()
    return [
        Post(
            id=post_id, date=parser.dates.get(post_id), title=parser.titles.get(post_id)
        )
        for post_id in parser.order
    ]


def sanitize_title(title: str) -> str:
    """タイトルをファイル名に使える形に整える。

    改行や連続する空白は 1 つの半角スペースにまとめ、使えない文字は `_` に
    置き換える。見た目を保ちたいので、記号を広く落とすことはしない。
    """
    collapsed = " ".join(title.split())
    return _UNSAFE_RE.sub("_", collapsed).strip(" .")


def truncate_bytes(text: str, limit: int) -> str:
    """UTF-8 で limit バイトに収まるよう、文字境界を壊さずに切り詰める。"""
    encoded = text.encode("utf-8")
    if len(encoded) <= limit:
        return text
    return encoded[:limit].decode("utf-8", "ignore").rstrip()


def build_filename(post: Post, ext: str = DEFAULT_EXT) -> str | None:
    """`<日付>_<タイトル>.<拡張子>` を組み立てる。日付が無ければ None。

    タイトルが取れない投稿がまれにあるので、その場合はタイトルの代わりに id を
    使う。日付だけにはしない。同じ日付の投稿が 2 件あると同名になり、video_dl
    が 2 件目を取得済みと見なして黙ってスキップしてしまうため。
    """
    if not post.date:
        return None
    label = sanitize_title(post.title) if post.title else ""
    budget = MAX_NAME_BYTES - len(f"{post.date}_.{ext}".encode())
    return f"{post.date}_{truncate_bytes(label or post.id, budget)}.{ext}"


def format_line(post: Post, ext: str = DEFAULT_EXT) -> str:
    """ids.txt の 1 行を作る。ファイル名を作れなければ id だけの行にする。"""
    name = build_filename(post, ext)
    return f"{post.id}\t{name}" if name else post.id


def read_source(source: str) -> str:
    """`-` なら標準入力、それ以外はファイルパスとして読む。"""
    if source == "-":
        return sys.stdin.read()
    return Path(source).read_text(encoding="utf-8")


if __name__ == "__main__":
    import argparse

    parser_ = argparse.ArgumentParser(
        description=(
            "投稿一覧ページの HTML から id と保存ファイル名を抜き出し、"
            "タブ区切りで標準出力に書く（そのまま ids.txt へ追記できる）。"
        ),
    )
    parser_.add_argument(
        "source",
        nargs="?",
        default="-",
        help="HTML ファイルのパス（省略時および - で標準入力から読む）",
    )
    parser_.add_argument(
        "--ext",
        default=DEFAULT_EXT,
        help=f"ファイル名に付ける拡張子（既定 {DEFAULT_EXT}）",
    )
    args = parser_.parse_args()

    try:
        source_html = read_source(args.source)
    except OSError as err:
        logger.error(f"HTML を読めません: {err}")
        raise SystemExit(1)

    posts = parse_posts(source_html)
    if not posts:
        logger.error(
            "投稿が 1 件も見つかりませんでした。"
            "/posts/<id> へのリンクを含む HTML か確認してください。"
        )
        raise SystemExit(1)

    incomplete = 0
    for item in posts:
        if not item.date:
            # 日付が無いとファイル名を作れないので、id だけの行になる。
            logger.warning(f"[WARN] {item.id} は日付が取れませんでした")
            incomplete += 1
        elif not item.title:
            logger.warning(
                f"[WARN] {item.id} はタイトルが取れませんでした。"
                "代わりに id をファイル名に使います"
            )
        print(format_line(item, args.ext))

    logger.info(f"{len(posts)} 件（うちファイル名を作れなかったもの {incomplete} 件）")
