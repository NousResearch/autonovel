#!/usr/bin/env python3
"""Generate doodles with proper transparent backgrounds."""

import torch
from diffusers import StableDiffusionPipeline
from PIL import Image, ImageChops
import os
import sys
import collections

local_path = os.path.expanduser('~/.cache/huggingface/hub/models--Lykon--dreamshaper-8/snapshots/a7e52b98680b1ba8ff7bce97c7f9f2e2e5337917')
output_dir = os.path.expanduser('~/autonovel/books/mdim-book3/doodles/book1')
os.makedirs(output_dir, exist_ok=True)

print('Loading model...')
pipe = StableDiffusionPipeline.from_pretrained(
    local_path, torch_dtype=torch.float32, safety_checker=None, local_files_only=True
)
pipe = pipe.to('cpu')
print('Model loaded!\n')

def flood_fill_transparency(img, seed_point=(0,0), threshold=30):
    """Use flood fill from corners to make background transparent."""
    img = img.convert('RGBA')
    width, height = img.size
    pixels = img.load()
    
    # Get the background color from the corner
    bg_color = pixels[seed_point[0], seed_point[1]]
    
    # BFS flood fill from all 4 corners
    visited = set()
    queue = collections.deque()
    
    # Add all 4 corners as starting points
    corners = [(0,0), (width-1,0), (0,height-1), (width-1,height-1)]
    for corner in corners:
        if corner not in visited:
            queue.append(corner)
            visited.add(corner)
    
    while queue:
        x, y = queue.popleft()
        pixel = pixels[x, y]
        
        # Check if this pixel is similar to the background
        if (abs(pixel[0] - bg_color[0]) < threshold and
            abs(pixel[1] - bg_color[1]) < threshold and
            abs(pixel[2] - bg_color[2]) < threshold and
            pixel[3] > 0):  # Not already transparent
            
            # Make transparent
            pixels[x, y] = (255, 255, 255, 0)
            
            # Add neighbors
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < width and 0 <= ny < height and (nx,ny) not in visited:
                    visited.add((nx,ny))
                    queue.append((nx,ny))
    
    return img

# Test with first doodle
prompt = "Simple black line doodle of a bowl of lumpy oatmeal with a frowny face drawn on the side. Steam rising as tiny fists. Childlike hand-drawn sketch, Diary of a Wimpy Kid style. Thick black pen strokes on bright white paper. Monochrome. No shading. Very clean simple lines."
negative = "color, shading, gradient, realistic, photographic, 3D, complex, detailed, dark background, gray background, colored background, watermark, blurry"

print('Generating test doodle...')
image = pipe(prompt, negative_prompt=negative, num_inference_steps=8, guidance_scale=7.5, height=512, width=512).images[0]

# Apply flood fill transparency
img = flood_fill_transparency(image, threshold=35)

# Check result
px = img.load()
transparent = sum(1 for x in range(512) for y in range(512) if px[x,y][3] == 0)
pct = transparent * 100 // (512*512)

test_path = os.path.join(output_dir, 'TEST_transparent.png')
img.save(test_path, 'PNG')
print(f'Test saved: {test_path} ({pct}% transparent)')
print(f'Corner pixel: {px[0,0]}')
print(f'Center pixel: {px[256,256]}')
