import os
from pathlib import Path

import torch
from diffusers import StableDiffusionPipeline

from musabi_ml.image import write_title


def main() -> None:
    model_id = "XpucT/Deliberate"
    device = "cuda"
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
    ).to(device)
    generate_params = {
        "prompt": os.environ.get("PROMPT", "real photo"),
        "negative_prompt": os.environ.get("NEGATIVE_PROMPT", ""),
        "width": int(os.environ.get("WIDTH", "1080")),
        "height": int(os.environ.get("HEIGHT", "1080")),
        "num_images_per_prompt": 1,
    }
    images = pipe(**generate_params).images
    output_path = Path("/opt/ml/processing/output")
    for i, origin_image in enumerate(images):
        title = os.environ.get("DISH_NAME", "")
        write_title(
            origin_image.copy(),
            title,
        ).save(output_path / f"{i}_image_1.png")
        origin_image.save(output_path / f"{i}_image_2.png")


if __name__ == "__main__":
    main()
