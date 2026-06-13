#!/usr/bin/env python3
"""Generate doodles: 256x256 generation + rembg + upscale to 512x512."""

import torch
from diffusers import StableDiffusionPipeline
from PIL import Image, ImageFilter
import os
import sys

local_path = os.path.expanduser('~/.cache/huggingface/hub/models--Lykon--dreamshaper-8/snapshots/a7e52b98680b1ba8ff7bce97c7f9f2e2e5337917')
output_dir = os.path.expanduser('~/autonovel/books/mdim-book3/doodles/book1')
os.makedirs(output_dir, exist_ok=True)

print('Loading model...')
pipe = StableDiffusionPipeline.from_pretrained(
    local_path, torch_dtype=torch.float32, safety_checker=None, local_files_only=True
)
pipe = pipe.to('cpu')
print('Model loaded!')

# Try importing rembg
try:
    from rembg import remove as remove_bg
    HAS_REMBG = True
    print('rembg available for background removal')
except ImportError:
    HAS_REMBG = False
    print('rembg not available, using simple threshold')

def remove_background(img):
    """Remove background using rembg or fallback."""
    if HAS_REMBG:
        return remove_bg(img)
    else:
        # Simple threshold fallback
        img = img.convert('RGBA')
        datas = img.getdata()
        new_data = []
        for item in datas:
            if item[0] > 200 and item[1] > 200 and item[2] > 200:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        img.putdata(new_data)
        return img

# Test with first doodle at 256x256
prompt = "Simple black line doodle of a bowl of lumpy oatmeal with a frowny face. Steam rising as tiny fists. Childlike hand-drawn sketch, Diary of a Wimpy Kid style. Thick black pen on white paper. Monochrome."
negative = "color, shading, gradient, realistic, photographic, 3D, complex, dark background, gray background, watermark, blurry"

print('\nGenerating test at 256x256...')
image = pipe(prompt, negative_prompt=negative, num_inference_steps=6, guidance_scale=7.5, height=256, width=256).images[0]

print('Removing background...')
img = remove_background(image)

print('Upscaling to 512x512...')
img = img.resize((512, 512), Image.LANCZOS)

# Check result
px = img.load()
transparent = sum(1 for x in range(512) for y in range(512) if px[x,y][3] == 0)
pct = transparent * 100 // (512*512)

test_path = os.path.join(output_dir, 'TEST_256_upscaled.png')
img.save(test_path, 'PNG')
print(f'Test saved: {test_path}')
print(f'Size: {img.size}, Mode: {img.mode}')
print(f'Transparent: {pct}%')
print(f'Corner: {px[0,0]}, Center: {px[256,256]}')
