#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import glob
from PIL import Image, ExifTags
from inky.auto import auto
from gpiozero import Button
from signal import pause
import requests

# Add this import and registration for HEIC support
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    print("Warning: pillow-heif not installed. HEIC images will not be supported.")

SW_A = 5   # Next photo
SW_B = 6   # Rotate 90
SW_C = 16  # Rotate 180
SW_D = 24  # Toggle orientation

# Global state
current_image_path = None
current_image = None
current_rotation = 0
landscape = True

image_folder = "/home/tee/photos"  # Change to your image folder
image_paths = []
current_index = 0

IMMICH_URL = "http://10.0.1.41:30041"
API_KEY = "Emwmkf7IzakSyEYJAM8FvZGhX27kNRQjydh0nagY"
TEMP_IMAGE_PATH = "/tmp/current_frame.jpg"

def auto_orient(image):
    try:
        exif = image._getexif()
        if exif is not None:
            for tag, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag, tag)
                if tag_name == "Orientation":
                    if value == 3:
                        image = image.rotate(180, expand=True)
                    elif value == 6:
                        image = image.rotate(270, expand=True)
                    elif value == 8:
                        image = image.rotate(90, expand=True)
                    break
    except Exception:
        pass
    return image

def display_image(image_path):

    try:
        inky_display = auto(ask_user=True, verbose=True)
        print(f"Detected display: {inky_display.width} x {inky_display.height}")

        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            return False
        
        image = Image.open(image_path)
        image = auto_orient(image)
        print(f"Image loaded: {image_path} (size: {image.size}) ")

        display_width, display_height = inky_display.width, inky_display.height
        print(f"Display size: {display_width},{display_height}")

        scale_w = display_width / image.width
        scale_h = display_height / image.height
        scale = min(scale_w, scale_h)

        #Resize
        new_width = int(image.width * scale)
        new_height = int(image.height * scale)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        #Create a new image with the display dimensions and paste the resized image
        display_image = Image.new('RGB', (display_width, display_height), (255, 255, 255))
        paste_x = (display_width - new_width) // 2
        paste_y = (display_height - new_height) // 2
        display_image.paste(image, (paste_x, paste_y))

        #Set the image on the display
        inky_display.set_image(display_image)

        print("Updating display...")
        inky_display.show()
        return True

    except Exception as e:
        print(f"Error displaying image: {e}")
        return False

def load_image_list():
    global image_paths
    # Find jpg, png, heic files
    image_paths = sorted(
        glob.glob(os.path.join(image_folder, "*.jpg")) +
        glob.glob(os.path.join(image_folder, "*.jpeg")) +
        glob.glob(os.path.join(image_folder, "*.png")) +
        glob.glob(os.path.join(image_folder, "*.heic"))
    )
    print(f"Found {len(image_paths)} images.")

def fetch_random_photo():
    headers = {"x-api-key": API_KEY}
    try:
        # Get a random asset
        resp = requests.get(f"{IMMICH_URL}/api/assets/random?count=1", headers=headers)
        resp.raise_for_status()
        assets = resp.json()
        if not assets:
            print("No assets returned from Immich.")
            return None
        asset = assets[0]
        if asset["type"].upper() == "VIDEO" or asset["originalFileName"].lower().endswith(".mov"):
            print("Random asset is a video, skipping.")
            return None
        asset_id = asset["id"]
        # Download the asset
        img_resp = requests.get(f"{IMMICH_URL}/api/asset/file/{asset_id}", headers=headers)
        img_resp.raise_for_status()
        with open(TEMP_IMAGE_PATH, "wb") as f:
            f.write(img_resp.content)
        print(f"Downloaded image to {TEMP_IMAGE_PATH}")
        return TEMP_IMAGE_PATH
    except Exception as e:
        print(f"Error fetching photo from Immich: {e}")
        return None

def load_next_photo():
    global current_image_path, current_image, current_rotation, current_index
    if not image_paths:
        print("No images found.")
        return
    current_index = (current_index + 1) % len(image_paths)
    current_image_path = image_paths[current_index]
    print(f"Next photo button pressed. Loading: {current_image_path}")
    current_rotation = 0
    current_image = Image.open(current_image_path)
    display_and_show()

def rotate_90():
    global current_image, current_rotation
    print("Rotate 90 button pressed.")
    current_rotation = (current_rotation + 90) % 360
    current_image = current_image.rotate(90, expand=True)
    display_and_show()

def rotate_180():
    global current_image, current_rotation
    print("Rotate 180 button pressed.")
    current_rotation = (current_rotation + 180) % 360
    current_image = current_image.rotate(180, expand=True)
    display_and_show()

def toggle_orientation():
    global landscape
    print("Toggle orientation button pressed.")
    landscape = not landscape
    display_and_show()

def display_and_show():
    global current_image, landscape
    inky_display = auto(ask_user=True, verbose=True)
    display_width, display_height = inky_display.width, inky_display.height

    # Swap width/height if portrait
    if not landscape:
        display_width, display_height = display_height, display_width

    image = auto_orient(current_image)
    scale_w = display_width / image.width
    scale_h = display_height / image.height
    scale = min(scale_w, scale_h)
    new_width = int(image.width * scale)
    new_height = int(image.height * scale)
    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    display_image = Image.new('RGB', (display_width, display_height), (255, 255, 255))
    paste_x = (display_width - new_width) // 2
    paste_y = (display_height - new_height) // 2
    display_image.paste(image, (paste_x, paste_y))
    inky_display.set_image(display_image)
    inky_display.show()

if __name__ == "__main__":
    img_path = fetch_random_photo()
    if not img_path:
        print("Could not fetch initial photo from Immich.")
        exit(1)
    current_image_path = img_path
    current_image = Image.open(current_image_path)
    display_and_show()
    btn_a = Button(SW_A)
    btn_b = Button(SW_B)
    btn_c = Button(SW_C)
    btn_d = Button(SW_D)
    btn_a.when_pressed = load_next_photo
    btn_b.when_pressed = rotate_90
    btn_c.when_pressed = rotate_180
    btn_d.when_pressed = toggle_orientation
    print("Ready for button input. Press Ctrl+C to exit.")
    pause()