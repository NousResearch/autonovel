#!/usr/bin/env python3
"""Generate doodles for MDIM Book 1.
Strategy: generate at 256x256 with white bg prompt, then threshold to keep only dark lines."""

import torch
from diffusers import StableDiffusionPipeline
from PIL import Image
import os
import sys
import numpy as np

local_path = os.path.expanduser('~/.cache/huggingface/hub/models--Lykon--dreamshaper-8/snapshots/a7e52b98680b1ba8ff7bce97c7f9f2e2e5337917')
output_dir = os.path.expanduser("~/autonovel/books/mdim-book3/doodles/book1")
os.makedirs(output_dir, exist_ok=True)

print('Loading model...')
pipe = StableDiffusionPipeline.from_pretrained(
    local_path, torch_dtype=torch.float32, safety_checker=None, local_files_only=True
)
pipe = pipe.to('cpu')
print('Model loaded!\n')

def extract_lines(img, threshold=120):
    """Keep only dark pixels (lines), make everything else transparent.
    Uses numpy for speed."""
    img = img.convert('RGB')
    arr = np.array(img)  # shape: (H, W, 3)
    
    # Calculate brightness (max of RGB gives good contrast for black lines)
    brightness = arr.max(axis=2)  # shape: (H, W)
    
    # Create RGBA output
    rgba = np.zeros((*brightness.shape, 4), dtype=np.uint8)
    
    # Dark pixels (below threshold) become black and opaque
    mask = brightness < threshold
    rgba[mask, :3] = 0  # Black lines
    rgba[mask, 3] = 255  # Opaque
    
    # Light pixels become transparent
    rgba[~mask, :] = 0  # All zeros = transparent
    
    return Image.fromarray(rgba, 'RGBA')

doodles = [
    ("ch01_sticky_sadness.png",
     "Simple black line doodle of a bowl of lumpy oatmeal with a frowny face. Steam rising as tiny fists. Childlike hand-drawn sketch, Diary of a Wimpy Kid style. Black pen on white paper. Monochrome. Clean simple lines. No border."),
    ("ch02_column_of_shame.png",
     "Simple black line doodle of a tall stone column with a child's juice box on top. A tiny ginger cat sitting on the juice box. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch03_mud_trail.png",
     "Simple black line doodle of messy paw-shaped mud blobs leading into a dark archway. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch04_cat_salami_jetpack.png",
     "Simple black line doodle of a tiny ginger cat with a salami jetpack flying over a picnic. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch05_ledger.png",
     "Simple black line doodle of a secret ledger page with columns and tiny handwriting. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch06_pigeon_spy.png",
     "Simple black line doodle of a disheveled pigeon on a fence wearing a tiny spy hat. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch07_lulu_chaos.png",
     "Simple black line doodle of a little girl spinning with food on her face, toys flying. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch08_henry_ride.png",
     "Simple black line doodle of a majestic horse with a tiny girl and bulldog on its back. Horse has a superhero cape. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch09_mud_crosssection.png",
     "Simple black line doodle of a cross-section diagram of mud layers with labels. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch10_sub_salami.png",
     "Simple black line doodle of a cross-section of a tiny submarine. A salami in the pilot seat wearing goggles. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch11_canal_map.png",
     "Simple black line doodle of a treasure map with canal tunnels, X marks and labels. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch12_simba_grate.png",
     "Simple black line doodle of a ginger cat's face through a metal grate. Fuzzy ginger monster with glowing eyes. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch13_mission_impossible.png",
     "Simple black line doodle of a Mission Impossible diagram with horse pulling mat and salami on rope. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch14_cat_dar.png",
     "Simple black line doodle of a girl behind a Cat-Dar science project. Teacher looks confused. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch15_boathouse.png",
     "Simple black line doodle of boathouse interior with monitors and a plush cat throne. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch16_simba_throne.png",
     "Simple black line doodle of a ginger cat on a velvet cushion looking down at a tiny girl and bulldog. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch17_soy_sauce.png",
     "Simple black line doodle of a soy sauce mushroom cloud. Ginger cat and doberman looking shocked. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch18_sinkhole.png",
     "Simple black line doodle of a sinkhole entrance with rusted iron arches and dangling glass. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch19_salami_rescue.png",
     "Simple black line doodle of a giant salami hanging on a rope over a crack. Bulldog holding the tail. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch20_salami_bobsled.png",
     "Simple black line doodle of three characters on a salami bobsled going down a pipe. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch21_simba_entrance.png",
     "Simple black line doodle of a ginger cat at a grand entrance with two cat guards. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch22_salami_sensors.png",
     "Simple black line doodle of a giant salami in the middle of alarm sensors. Bulldog sitting on it like a king. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch23_pipe_slide.png",
     "Simple black line doodle of three characters falling down a metal pipe with towels. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch24_henry_hero.png",
     "Simple black line doodle of a horse nudging a giant salami onto a silver platter. Humans cheering. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
    ("ch25_shadow_cat.png",
     "Simple black line doodle of a girl and bulldog looking at a park. A ginger cat watching from shadows. Childlike hand-drawn sketch. Black pen on white paper. Monochrome. No border."),
]

negative_prompt = "color, shading, gradient, realistic, photographic, 3D, complex, detailed, dark background, gray background, colored background, watermark, blurry, multiple images, text, words, letters, border, frame"

total = len(doodles)
for i, (filename, prompt) in enumerate(doodles, 1):
    filepath = os.path.join(output_dir, filename)
    
    print(f'[{i}/{total}] {filename}...')
    sys.stdout.flush()
    
    try:
        image = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=6,
            guidance_scale=7.5,
            height=256,
            width=256,
            generator=torch.Generator("cpu").manual_seed(42 + i)
        ).images[0]
        
        # Extract dark lines, make background transparent
        img = extract_lines(image, threshold=100)
        
        # Upscale to 512x512
        img = img.resize((512, 512), Image.LANCZOS)
        
        # Save
        img.save(filepath, 'PNG')
        
        # Quick quality check
        arr = np.array(img)
        opaque = np.count_nonzero(arr[:,:,3])
        total_px = 512*512
        print(f'  OK: {opaque} opaque pixels ({opaque*100//total_px}%)')
        sys.stdout.flush()
        
    except Exception as e:
        print(f'  ERROR: {e}', file=sys.stderr)

print(f'\nAll doodles saved to: {output_dir}')
