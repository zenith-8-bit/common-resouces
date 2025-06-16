import time
import numpy as np # Not strictly needed for this version, but kept for consistency
from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1306, sh1106 # Or just ssd1306 if you know your chip
from PIL import Image # Import Image module for loading and processing images
import os # To check if the file exists

# --- Configuration for SPI ---
# SPI uses a bus (0 or 1) and device (0 or 1, for CS0 or CS1)
# Most common setup is bus 0, device 0 (CE0)
SPI_BUS = 0
SPI_DEVICE = 0 # Corresponds to CE0 (GPIO 8)

# GPIO pin numbers for DC and RESET (using BCM numbering)
# Ensure these match your wiring!
DC_PIN = 23    # Connected to GPIO 23 (Physical Pin 16)
RST_PIN = 24  # Connected to GPIO 24 (Physical Pin 18)

# --- OLED Device Initialization ---
device = None # Initialize device to None
try:
    serial = spi(port=SPI_BUS, device=SPI_DEVICE, gpio_DC=DC_PIN, gpio_RST=RST_PIN)
    device = ssd1306(serial) # Attempt to initialize SSD1306
    print(f"OLED display initialized: {device.width}x{device.height}")
except Exception as e:
    print(f"Error initializing OLED device: {e}")
    print("Please ensure your wiring is correct and the luma.oled library is installed.")
    print("Exiting as display device could not be initialized.")
    exit() # Exit if device cannot be initialized, as it's critical

# --- Image Loading and Processing ---
IMAGE_PATH = 'image_b18dae.png' # The path to your uploaded image

def load_and_process_eye_image(image_path, display_width, display_height):
    """
    Loads an image, crops a single eye, resizes it, and converts it to 1-bit monochrome.
    
    Args:
        image_path (str): Path to the source image (e.g., GIF or PNG).
        display_width (int): Target width for the processed image (OLED width).
        display_height (int): Target height for the processed image (OLED height).
        
    Returns:
        PIL.Image.Image: A 1-bit monochrome PIL Image ready for display, or None if error.
    """
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return None

    try:
        img = Image.open(image_path)
        print(f"Loaded image '{image_path}' with size: {img.size}, mode: {img.mode}")

        # Assuming the image contains two eyes and we want to crop one.
        # These coordinates are based on visual inspection of 'image_b18dae.png'
        # and aim to capture the right eye. Adjust if your image varies or if
        # you want the left eye.
        img_width, img_height = img.size
        
        # Define a bounding box for the right eye
        # (left_x, top_y, right_x, bottom_y)
        # Roughly the right eye from the uploaded PNG (692x400)
        # Adjust these values based on your specific image if it changes
        crop_box = (img_width // 2 + 50, img_height // 2 - 100, img_width - 100, img_height // 2 + 100)
        
        # Ensure crop box is within image bounds
        crop_box = (max(0, crop_box[0]), max(0, crop_box[1]),
                    min(img_width, crop_box[2]), min(img_height, crop_box[3]))
        
        print(f"Cropping image with box: {crop_box}")
        cropped_img = img.crop(crop_box)
        print(f"Cropped image size: {cropped_img.size}")

        # Resize the cropped image to fit the OLED display dimensions
        # Use Image.LANCZOS for high-quality downsampling
        resized_img = cropped_img.resize((display_width, display_height), Image.LANCZOS)
        print(f"Resized image size: {resized_img.size}")

        # Convert to 1-bit monochrome for the OLED display.
        # This converts pixels brighter than a threshold to white (1) and others to black (0).
        final_image = resized_img.convert('1')
        print("Image converted to 1-bit monochrome.")
        
        return final_image

    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None

def animate_image_on_oled(image_path):
    """
    Loads an image (or GIF frames) and animates them on the OLED display.
    For static images, it displays the processed image continuously.
    For GIFs, it iterates through frames.
    """
    processed_frames = []
    frame_durations = [] # In milliseconds

    try:
        # Open the image file
        img = Image.open(image_path)

        # Check if it's a multi-frame image (like a GIF)
        # PIL's is_animated property is reliable for GIFs
        if hasattr(img, 'is_animated') and img.is_animated:
            print(f"Detected animated image (GIF) with {img.n_frames} frames.")
            for i in range(img.n_frames):
                img.seek(i) # Go to the next frame
                # Get frame duration, default to 100ms if not specified
                duration_ms = img.info.get('duration', 100) 
                
                # Process the current frame (crop, resize, convert)
                # Apply the same logic for cropping a single eye as defined above.
                # NOTE: For an actual animated eye GIF, you might want to crop
                # the same region consistently or pre-process the GIF to contain
                # only the eye you want to animate.
                
                # For this example, we will just use the first frame if it's not a GIF
                # or process each frame if it is a GIF with the same cropping logic.
                
                # (Re-using the cropping logic from load_and_process_eye_image, adapted for frames)
                frame_img = img.copy() # Make a copy to process the current frame
                
                # Define a bounding box for the right eye for the current frame
                img_width, img_height = frame_img.size
                crop_box = (img_width // 2 + 50, img_height // 2 - 100, img_width - 100, img_height // 2 + 100)
                crop_box = (max(0, crop_box[0]), max(0, crop_box[1]),
                            min(img_width, crop_box[2]), min(img_height, crop_box[3]))
                            
                cropped_frame = frame_img.crop(crop_box)
                resized_frame = cropped_frame.resize((device.width, device.height), Image.LANCZOS)
                final_frame = resized_frame.convert('1')
                
                processed_frames.append(final_frame)
                frame_durations.append(duration_ms / 1000.0) # Convert ms to seconds
                
            print(f"Prepared {len(processed_frames)} frames for animation.")
            
        else:
            # It's a static image (like the provided PNG). Process it once.
            print(f"Detected static image. Processing single frame.")
            processed_single_frame = load_and_process_eye_image(image_path, device.width, device.height)
            if processed_single_frame:
                processed_frames.append(processed_single_frame)
                frame_durations.append(0.1) # Default short delay for static image display loop
            else:
                print("Failed to process image. Cannot animate.")
                return # Exit if image processing failed

    except Exception as e:
        print(f"Error loading or preparing image frames: {e}")
        return # Exit if frame preparation failed

    if not processed_frames:
        print("No frames to display. Exiting animation.")
        return

    # --- Animation Loop ---
    frame_index = 0
    while True:
        try:
            current_frame = processed_frames[frame_index]
            display_duration = frame_durations[frame_index]

            # Display the frame
            device.display(current_frame)
            time.sleep(display_duration)

            # Move to the next frame, loop back to start if end reached
            frame_index = (frame_index + 1) % len(processed_frames)

        except KeyboardInterrupt:
            raise # Re-raise KeyboardInterrupt to be caught by the main try-except block
        except Exception as e:
            print(f"Error during animation loop: {e}")
            break # Exit loop on other errors

# --- Main execution block ---
try:
    if device: # Only proceed if device was successfully initialized
        device.clear() # Clear the display at the very beginning
        print("Starting image animation on OLED...")
        animate_image_on_oled(IMAGE_PATH)

except KeyboardInterrupt:
    print("\nKeyboardInterrupt detected. Exiting animation.")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
finally:
    # This 'finally' block ensures the display is cleared upon script termination.
    if device: # Only clear if the device was actually initialized
        device.clear() # Send the clear command to turn off all pixels
        # Add a small delay to give the OLED controller time to process the clear command
        time.sleep(0.5)
        print("Display cleared and resources released.")
    else:
        print("Display device not initialized. No cleanup necessary.")

