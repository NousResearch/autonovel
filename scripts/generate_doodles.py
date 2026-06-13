#!/usr/bin/env python3
"""Generate doodle art for MDIM Book 1 using Stable Diffusion on CPU."""

import torch
from diffusers import DiffusionPipeline
import os

model_id = "Lykon/dreamshaper-8"
print(f"Loading model: {model_id}")

pipe = DiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float32,
    safety_checker=None,
    requires_safety_checker=False
)
pipe = pipe.to("cpu")
print("Model loaded! Generating doodles...")

doodles = [
    ("ch01_sticky_sadness.png", 
     "Simple black line doodle of a bowl of lumpy oatmeal with a frowny face drawn on the side. Steam rising as tiny fists. Childlike hand-drawn sketch style, like Diary of a Wimpy Kid. Black pen only on white background. No shading, no color, simple lines only.",
     "A bowl of oats with a frowny face and the caption: STICKY SADNESS"),
    
    ("ch02_column_of_shame.png",
     "Simple black line doodle of a tall stone column with a child's juice box balanced on top. A tiny cat sitting on the juice box looking proud. Childlike hand-drawn sketch. Black pen only on white background.",
     "A Roman column with a child's juice box balanced on top. Caption: COLUMN OF SHAME"),
    
    ("ch03_mud_trail.png",
     "Simple black line doodle of messy paw-shaped mud blobs leading into a dark archway. Each blob is different sizes. Childlike hand-drawn sketch. Black pen only on white background.",
     "A trail of messy paw-shaped mud blobs leading into a dark archway. Caption: THE EVIDENCE"),
]

output_dir = os.path.expanduser("~/autonovel/books/mdim-book3/doodles")
os.makedirs(output_dir, exist_ok=True)

negative_prompt = "color, shading, gradient, realistic, photographic, 3D, complex, detailed, background, watermark, text, blurry"

for filename, prompt, caption in doodles:
    print(f"\nGenerating: {filename}")
    print(f"  Prompt: {prompt[:60]}...")
    
    image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=8,
        guidance_scale=7.5,
        height=512,
        width=512,
        generator=torch.Generator("cpu").manual_seed(42)
    ).images[0]
    
    output_path = os.path.join(output_dir, filename)
    image.save(output_path)
    print(f"  Saved: {output_path}")

print(f"\nAll doodles generated in: {output_dir}")
