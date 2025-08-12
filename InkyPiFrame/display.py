#!/usr/bin/env python3
import sys
import os
import requests
from PIL import Image, ExifTags
from inky.auto import auto
from gpiozero import Button
from gpiozero.pins.mock import MockFactory
from gpiozero import Device
from signal import pause

# Configuration
IMMICH_URL = "http://10.0.1.41:30041"
API_KEY = "Emwmkf7IzakSyEYJAM8FvZGhX27kNRQjydh0nagY"
TEMP_IMAGE_PATH = "/tmp/current_frame.jpg"

Device.pin_factory = None  # Reset any existing pin factory

# Button GPIO pins (BCM numbering)
SW_A = 12  # Next photo
SW_B = 13  # Rotate 90
SW_C = 20  # Rotate 180
SW_D = 21  # Toggle orientation

# Global state
current_image = None
current_rotation = 0
landscape = True

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

def fetch_random_photo():
    headers = {"x-api-key": API_KEY}
    max_attempts = 3
    
    for attempt in range(max_attempts):
        try:
            # Get random assets
            resp = requests.get(f"{IMMICH_URL}/api/assets/random?count=1", headers=headers)
            resp.raise_for_status()
            assets = resp.json()
            
            if not assets:
                print("No assets returned from Immich.")
                return None
                
            asset = assets[0]
            if asset["type"].upper() == "VIDEO" or asset["originalFileName"].lower().endswith((".mov", ".mp4")):
                print(f"Skipping video asset: {asset['originalFileName']}")
                continue
                
            # Use the correct endpoint for downloading
            img_resp = requests.get(f"{IMMICH_URL}/api/assets/download/{asset['id']}", headers=headers)
            img_resp.raise_for_status()
            
            with open(TEMP_IMAGE_PATH, "wb") as f:
                f.write(img_resp.content)
            print(f"Successfully downloaded image: {asset['originalFileName']}")
            return TEMP_IMAGE_PATH
            
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/{max_attempts} failed: {e}")
            if attempt == max_attempts - 1:
                print("Max attempts reached, giving up.")
                return None
            print("Retrying...")
    
    return None

def display_image(image_path):
    global current_image
    try:
        current_image = Image.open(image_path)
        display_and_show()
        return True
    except Exception as e:
        print(f"Error displaying image: {e}")
        return False

def load_next_photo():
    print("Fetching next photo...")
    img_path = fetch_random_photo()
    if img_path:
        display_image(img_path)

def rotate_90():
    global current_image, current_rotation
    if current_image:
        current_rotation = (current_rotation + 90) % 360
        current_image = current_image.rotate(90, expand=True)
        display_and_show()

def rotate_180():
    global current_image, current_rotation
    if current_image:
        current_rotation = (current_rotation + 180) % 360
        current_image = current_image.rotate(180, expand=True)
        display_and_show()

def toggle_orientation():
    global landscape
    if current_image:
        landscape = not landscape
        display_and_show()

def display_and_show():
    global current_image, landscape
    if not current_image:
        return
        
    inky_display = auto(ask_user=True, verbose=True)
    display_width, display_height = inky_display.width, inky_display.height
    
    if not landscape:
        display_width, display_height = display_height, display_width
        
    image = auto_orient(current_image)
    scale = min(display_width / image.width, display_height / image.height)
    new_size = (int(image.width * scale), int(image.height * scale))
    image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    display_image = Image.new('RGB', (display_width, display_height), (255, 255, 255))
    paste_x = (display_width - new_size[0]) // 2
    paste_y = (display_height - new_size[1]) // 2
    display_image.paste(image, (paste_x, paste_y))
    
    inky_display.set_image(display_image)
    inky_display.show()

if __name__ == "__main__":
    # Set up buttons
    try:
        btn_a = Button(SW_A, pull_up=True)
        btn_b = Button(SW_B, pull_up=True)
        btn_c = Button(SW_C, pull_up=True)
        btn_d = Button(SW_D, pull_up=True)
        
        btn_a.when_pressed = load_next_photo
        btn_b.when_pressed = rotate_90
        btn_c.when_pressed = rotate_180
        btn_d.when_pressed = toggle_orientation
    except Exception as e:
        print(f"Error setting up buttons: {e}")
    
    # If path provided, display that image
    if len(sys.argv) > 1:
        success = display_image(sys.argv[1])
        sys.exit(0 if success else 1)
    else:
        # Otherwise, fetch initial photo and wait for button presses
        load_next_photo()
        print("Ready for button input. Press Ctrl+C to exit.")
        pause()