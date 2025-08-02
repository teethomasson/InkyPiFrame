#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from PIL import Image
from inky.auto import auto

def display_image(image_path):

    try:
        inky_display = auto(ask_user=True, verbose=True)
        print(f"Detected display: {inky_display.display_name}")

        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            return False
        
        image = Image.open(image_path)
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

    if __name__ == "__main__":
        if len(sys.argv) != 2:
           print("Usage: python3 display_image.py <image_path>")
           sys.exit(1)

    image_path = sys.argv[1]
    success = display_image(image_path)
    sys.exit(0 if success else 1)