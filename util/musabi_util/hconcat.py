import argparse
import os
from pathlib import Path

from PIL import Image


def concat_horizontal(
    left_path: str,
    right_path: str,
    output_path: str,
) -> None:
    """
    2枚の画像を横に並べて結合し、1枚の画像として保存します。

    高さが異なる場合は、高い方に合わせて低い方をアスペクト比を保ったまま
    リサイズしてから結合します。

    Args:
        left_path (str): 左側に配置する画像のパス
        right_path (str): 右側に配置する画像のパス
        output_path (str): 出力画像のパス
    """

    left = Image.open(left_path)
    right = Image.open(right_path)

    target_height = max(left.height, right.height)

    def resize_to_height(img: Image.Image, height: int) -> Image.Image:
        if img.height == height:
            return img
        width = int(round(img.width * height / img.height))
        return img.resize((width, height), Image.LANCZOS)

    left = resize_to_height(left, target_height)
    right = resize_to_height(right, target_height)

    output = Image.new(
        "RGB", (left.width + right.width, target_height), (255, 255, 255)
    )
    output.paste(left, (0, 0))
    output.paste(right, (left.width, 0))
    output.save(output_path)

    print(f"成功: {output_path} に保存しました。")
    print(f"  - 出力サイズ: {output.width}x{output.height}")


if __name__ == "__main__":
    default_dir = Path.home() / "Downloads"

    parser = argparse.ArgumentParser(
        description="2枚の画像を横に並べて結合する",
    )
    parser.add_argument(
        "--left",
        default=str(default_dir / "input-l.jpg"),
        help="左側に配置する画像のパス",
    )
    parser.add_argument(
        "--right",
        default=str(default_dir / "input-r.jpg"),
        help="右側に配置する画像のパス",
    )
    parser.add_argument(
        "--output",
        default=str(default_dir / "output.jpg"),
        help="出力画像のパス",
    )
    args = parser.parse_args()

    if not os.path.exists(args.left):
        print(f"エラー: 入力ファイル '{args.left}' が見つかりません。")
    elif not os.path.exists(args.right):
        print(f"エラー: 入力ファイル '{args.right}' が見つかりません。")
    else:
        concat_horizontal(args.left, args.right, args.output)
