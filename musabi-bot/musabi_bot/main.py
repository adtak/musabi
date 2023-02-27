import os

import torch
from diffusers import StableDiffusionPipeline


def main() -> None:
    model_id = "dreamlike-art/dreamlike-photoreal-2.0"
    device = "cuda"
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id, torch_dtype=torch.float16
    ).to(device)
    generate_params = {
        "prompt": os.environ.get("PROMPT", "real photo"),
        "negative_prompt": os.environ.get("NEGATIVE_PROMPT", ""),
        "width": int(os.environ.get("WIDTH", "1080")),
        "height": int(os.environ.get("HEIGHT", "1080")),
        # "max_embeddings_multiples": 2,
        # "num_inference_steps": 30,
        # "guidance_scale": 10,
        "num_images_per_prompt": 1,
    }
    images = pipe(**generate_params).images
    for i, image in enumerate(images):
        image.save(f"/opt/ml/processing/output/test_{i}.png")


if __name__ == "__main__":
    main()
