import time
import numpy as np # For random functions
from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1306, sh1106 # Or just ssd1306 if you know your chip
from PIL import ImageDraw
import random # Used for more varied random choices

# --- Configuration for SPI ---
# SPI uses a bus (0 or 1) and device (0 or 1, for CS0 or CS1)
# Most common setup is bus 0, device 0 (CE0)
SPI_BUS = 0
SPI_DEVICE = 0 # Corresponds to CE0 (GPIO 8)

# GPIO pin numbers for DC and RESET (using BCM numbering)
# Ensure these match your wiring!
DC_PIN = 23    # Connected to GPIO 23 (Physical Pin 16)
RST_PIN = 24  # Connected to GPIO 24 (Physical Pin 18)

# Initialize the OLED device.
# This part is wrapped in a try-except block to gracefully handle cases
# where the hardware might not be connected or configured correctly.
try:
    serial = spi(port=SPI_BUS, device=SPI_DEVICE, gpio_DC=DC_PIN, gpio_RST=RST_PIN)
    # Try ssd1306 first, if it doesn't work, you might need to change to sh1106(serial)
    device = ssd1306(serial)
except Exception as e:
    print(f"Error initializing OLED device: {e}")
    print("Please ensure your wiring is correct and the luma.oled library is installed.")
    print("If you are running this without an actual OLED, you'll need a mock device or to comment out device interaction.")
    # Exit the script if the device cannot be initialized, as further operations would fail.
    exit()

# Calculate center for eye placement based on the display resolution
center_x = device.width // 2
center_y = device.height // 2

# Define eye parameters for cute anime eyes. These values are tuned for a 128x64 display.
# Adjust them if your display has a different resolution or if you want a different look.
EYE_WIDTH = 28 # Half width of the eye ellipse (horizontal radius)
EYE_HEIGHT = 22 # Half height of the eye ellipse (vertical radius, taller for anime look)
PUPIL_SIZE = 8 # Radius of the pupil, made larger for more expression
HIGHLIGHT_SIZE = 2 # Size of the pupil highlight, a small black dot on the white pupil

# Eye positions (left and right eyes relative to the center of the screen)
LEFT_EYE_OFFSET_X = -30 # Moves the left eye further to the left
RIGHT_EYE_OFFSET_X = 30 # Moves the right eye further to the right
EYE_OFFSET_Y = 0 # Adjusts vertical position of both eyes (0 means centered vertically)

def draw_anime_eye(draw, center_x_eye, center_y_eye, pupil_x_offset=0, pupil_y_offset=0, highlight_pos='top_left'):
    """
    Draws a single cute anime eye with a pupil and a highlight.
    The highlight_pos parameter controls where the highlight appears within the pupil.
    
    Args:
        draw: The PIL ImageDraw object to draw on.
        center_x_eye (int): X-coordinate of the center of the eye.
        center_y_eye (int): Y-coordinate of the center of the eye.
        pupil_x_offset (int): Horizontal offset for the pupil relative to the eye center.
        pupil_y_offset (int): Vertical offset for the pupil relative to the eye center.
        highlight_pos (str): Position of the pupil highlight ('top_left', 'top_right',
                             'bottom_left', 'bottom_right', 'center').
    """
    # Draw the outer eye ellipse. This forms the main white sclera (or eye-white) shape.
    # It's filled black to create a cutout effect on the OLED, revealing the pupil.
    draw.ellipse(
        (center_x_eye - EYE_WIDTH, center_y_eye - EYE_HEIGHT,
         center_x_eye + EYE_WIDTH, center_y_eye + EYE_HEIGHT),
        outline="white", fill="black"
    )

    # Calculate the pupil's center based on eye center and its offset
    pupil_center_x = center_x_eye + pupil_x_offset
    pupil_center_y = center_y_eye + pupil_y_offset
    
    # Draw the pupil. This is a white circle/ellipse inside the black eye shape.
    draw.ellipse(
        (pupil_center_x - PUPIL_SIZE, pupil_center_y - PUPIL_SIZE,
         pupil_center_x + PUPIL_SIZE, pupil_center_y + PUPIL_SIZE),
        outline="white", fill="white"
    )

    # Calculate the highlight's position. This is a small black dot on the white pupil,
    # giving it a shiny, reflective look characteristic of anime eyes.
    highlight_x = pupil_center_x
    highlight_y = pupil_center_y

    # Adjust highlight position based on the 'highlight_pos' argument
    if highlight_pos == 'top_left':
        highlight_x -= PUPIL_SIZE // 2 # Move left
        highlight_y -= PUPIL_SIZE // 2 # Move up
    elif highlight_pos == 'top_right':
        highlight_x += PUPIL_SIZE // 2 - HIGHLIGHT_SIZE # Move right
        highlight_y -= PUPIL_SIZE // 2 # Move up
    elif highlight_pos == 'bottom_left':
        highlight_x -= PUPIL_SIZE // 2 # Move left
        highlight_y += PUPIL_SIZE // 2 - HIGHLIGHT_SIZE # Move down
    elif highlight_pos == 'bottom_right':
        highlight_x += PUPIL_SIZE // 2 - HIGHLIGHT_SIZE # Move right
        highlight_y += PUPIL_SIZE // 2 - HIGHLIGHT_SIZE # Move down
    elif highlight_pos == 'center':
        highlight_x -= HIGHLIGHT_SIZE // 2 # Center horizontally
        highlight_y -= HIGHLIGHT_SIZE // 2 # Center vertically

    # Draw the pupil highlight
    draw.ellipse(
        (highlight_x, highlight_y,
         highlight_x + HIGHLIGHT_SIZE, highlight_y + HIGHLIGHT_SIZE),
        fill="black" # Highlight is black on white pupil, for contrast on OLED
    )

def draw_closed_eye(draw, center_x_eye, center_y_eye):
    """
    Draws a closed eye as a simple horizontal line.
    
    Args:
        draw: The PIL ImageDraw object to draw on.
        center_x_eye (int): X-coordinate of the center of the eye.
        center_y_eye (int): Y-coordinate of the center of the eye.
    """
    # A simple horizontal line represents a closed eye
    draw.line((center_x_eye - EYE_WIDTH, center_y_eye,
               center_x_eye + EYE_WIDTH, center_y_eye),
              fill="white", width=2)

def draw_happy_eyes(draw, highlight_pos='top_left'):
    """
    Draws happy eyes: slightly wider and pupils looking slightly upwards.
    
    Args:
        draw: The PIL ImageDraw object to draw on.
        highlight_pos (str): Position of the pupil highlight.
    """
    draw_anime_eye(draw, center_x + LEFT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y,
                   pupil_x_offset=0, pupil_y_offset=-PUPIL_SIZE // 3, highlight_pos=highlight_pos)
    draw_anime_eye(draw, center_x + RIGHT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y,
                   pupil_x_offset=0, pupil_y_offset=-PUPIL_SIZE // 3, highlight_pos=highlight_pos)

def draw_sad_eyes(draw, highlight_pos='center'):
    """
    Draws sad eyes: pupils looking downwards, simulating a heavy or droopy look.
    
    Args:
        draw: The PIL ImageDraw object to draw on.
        highlight_pos (str): Position of the pupil highlight.
    """
    draw_anime_eye(draw, center_x + LEFT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y,
                   pupil_x_offset=0, pupil_y_offset=PUPIL_SIZE // 2, highlight_pos=highlight_pos)
    draw_anime_eye(draw, center_x + RIGHT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y,
                   pupil_x_offset=0, pupil_y_offset=PUPIL_SIZE // 2, highlight_pos=highlight_pos)

def draw_surprised_eyes(draw):
    """
    Draws surprised eyes: wide open with smaller, centered pupils.
    This uses temporary parameters to make the eyes appear wider.
    
    Args:
        draw: The PIL ImageDraw object to draw on.
    """
    temp_eye_height = EYE_HEIGHT + 5 # Make eyes a bit taller for surprise effect
    temp_pupil_size = PUPIL_SIZE // 2 # Smaller pupil for surprised look

    # Draw the outer eye ellipses with increased height
    draw.ellipse(
        (center_x + LEFT_EYE_OFFSET_X - EYE_WIDTH, center_y + EYE_OFFSET_Y - temp_eye_height,
         center_x + LEFT_EYE_OFFSET_X + EYE_WIDTH, center_y + EYE_OFFSET_Y + temp_eye_height),
        outline="white", fill="black"
    )
    draw.ellipse(
        (center_x + RIGHT_EYE_OFFSET_X - EYE_WIDTH, center_y + EYE_OFFSET_Y - temp_eye_height,
         center_x + RIGHT_EYE_OFFSET_X + EYE_WIDTH, center_y + EYE_OFFSET_Y + temp_eye_height),
        outline="white", fill="black"
    )

    # Draw the smaller, centered pupils
    draw.ellipse(
        (center_x + LEFT_EYE_OFFSET_X - temp_pupil_size, center_y + EYE_OFFSET_Y - temp_pupil_size,
         center_x + LEFT_EYE_OFFSET_X + temp_pupil_size, center_y + EYE_OFFSET_Y + temp_pupil_size),
        outline="white", fill="white"
    )
    draw.ellipse(
        (center_x + RIGHT_EYE_OFFSET_X - temp_pupil_size, center_y + EYE_OFFSET_Y - temp_pupil_size,
         center_x + RIGHT_EYE_OFFSET_X + temp_pupil_size, center_y + EYE_OFFSET_Y + temp_pupil_size),
        outline="white", fill="white"
    )

    # Add a small, centered highlight for consistency
    draw.ellipse(
        (center_x + LEFT_EYE_OFFSET_X - HIGHLIGHT_SIZE//2, center_y + EYE_OFFSET_Y - HIGHLIGHT_SIZE//2,
         center_x + LEFT_EYE_OFFSET_X + HIGHLIGHT_SIZE//2, center_y + EYE_OFFSET_Y + HIGHLIGHT_SIZE//2),
        fill="black"
    )
    draw.ellipse(
        (center_x + RIGHT_EYE_OFFSET_X - HIGHLIGHT_SIZE//2, center_y + EYE_OFFSET_Y - HIGHLIGHT_SIZE//2,
         center_x + RIGHT_EYE_OFFSET_X + HIGHLIGHT_SIZE//2, center_y + EYE_OFFSET_Y + HIGHLIGHT_SIZE//2),
        fill="black"
    )

def draw_wink_eyes(draw, left_wink=True):
    """
    Draws a wink, with one eye closed and the other open.
    
    Args:
        draw: The PIL ImageDraw object to draw on.
        left_wink (bool): If True, the left eye winks; otherwise, the right eye winks.
    """
    if left_wink:
        draw_closed_eye(draw, center_x + LEFT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y)
        draw_anime_eye(draw, center_x + RIGHT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, highlight_pos='top_left')
    else:
        draw_anime_eye(draw, center_x + LEFT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, highlight_pos='top_left')
        draw_closed_eye(draw, center_x + RIGHT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y)

def draw_sleepy_eyes(draw):
    """
    Draws sleepy eyes: partially closed or with heavy lids, and pupils looking low.
    
    Args:
        draw: The PIL ImageDraw object to draw on.
    """
    # Simulate partially closed eyes by drawing a flattened ellipse
    draw.ellipse(
        (center_x + LEFT_EYE_OFFSET_X - EYE_WIDTH, center_y + EYE_OFFSET_Y - EYE_HEIGHT // 3,
         center_x + LEFT_EYE_OFFSET_X + EYE_WIDTH, center_y + EYE_OFFSET_Y + EYE_HEIGHT // 3),
        outline="white", fill="black"
    )
    draw.ellipse(
        (center_x + RIGHT_EYE_OFFSET_X - EYE_WIDTH, center_y + EYE_OFFSET_Y - EYE_HEIGHT // 3,
         center_x + RIGHT_EYE_OFFSET_X + EYE_WIDTH, center_y + EYE_OFFSET_Y + EYE_HEIGHT // 3),
        outline="white", fill="black"
    )
    # Pupils are small and positioned low to emphasize sleepiness
    draw.ellipse(
        (center_x + LEFT_EYE_OFFSET_X - PUPIL_SIZE // 2, center_y + EYE_OFFSET_Y + PUPIL_SIZE // 2,
         center_x + LEFT_EYE_OFFSET_X + PUPIL_SIZE // 2, center_y + EYE_OFFSET_Y + PUPIL_SIZE + HIGHLIGHT_SIZE),
        outline="white", fill="white"
    )
    draw.ellipse(
        (center_x + RIGHT_EYE_OFFSET_X - PUPIL_SIZE // 2, center_y + EYE_OFFSET_Y + PUPIL_SIZE // 2,
         center_x + RIGHT_EYE_OFFSET_X + PUPIL_SIZE // 2, center_y + EYE_OFFSET_Y + PUPIL_SIZE + HIGHLIGHT_SIZE),
        outline="white", fill="white"
    )

def animate_eyes():
    """
    Main animation loop that cycles through various eye movements and emotional states.
    It randomly selects a state and displays it for a random duration.
    """
    # Define a list of all possible eye states/emotions
    eye_states = [
        'normal_straight', 'normal_left', 'normal_right', 'normal_up', 'normal_down',
        'blink', 'happy', 'sad', 'surprised', 'wink_left', 'wink_right', 'sleepy'
    ]

    while True:
        # Randomly choose an eye state and a highlight position for variety
        state = random.choice(eye_states)
        highlight_choice = random.choice(['top_left', 'top_right', 'bottom_left', 'bottom_right', 'center'])

        # Use a 'with canvas(device) as draw:' block to ensure drawing operations are batched
        # and sent to the display efficiently.
        with canvas(device) as draw:
            if state == 'normal_straight':
                draw_anime_eye(draw, center_x + LEFT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, highlight_pos=highlight_choice)
                draw_anime_eye(draw, center_x + RIGHT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, highlight_pos=highlight_choice)
                time.sleep(np.random.uniform(1.0, 3.0)) # Stay in this state for a random duration
            elif state == 'normal_left':
                draw_anime_eye(draw, center_x + LEFT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, pupil_x_offset=-PUPIL_SIZE, highlight_pos=highlight_choice)
                draw_anime_eye(draw, center_x + RIGHT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, pupil_x_offset=-PUPIL_SIZE, highlight_pos=highlight_choice)
                time.sleep(np.random.uniform(0.5, 1.5))
            elif state == 'normal_right':
                draw_anime_eye(draw, center_x + LEFT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, pupil_x_offset=PUPIL_SIZE, highlight_pos=highlight_choice)
                draw_anime_eye(draw, center_x + RIGHT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, pupil_x_offset=PUPIL_SIZE, highlight_pos=highlight_choice)
                time.sleep(np.random.uniform(0.5, 1.5))
            elif state == 'normal_up':
                draw_anime_eye(draw, center_x + LEFT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, pupil_y_offset=-PUPIL_SIZE, highlight_pos=highlight_choice)
                draw_anime_eye(draw, center_x + RIGHT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, pupil_y_offset=-PUPIL_SIZE, highlight_pos=highlight_choice)
                time.sleep(np.random.uniform(0.5, 1.5))
            elif state == 'normal_down':
                draw_anime_eye(draw, center_x + LEFT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, pupil_y_offset=PUPIL_SIZE, highlight_pos=highlight_choice)
                draw_anime_eye(draw, center_x + RIGHT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, pupil_y_offset=PUPIL_SIZE, highlight_pos=highlight_choice)
                time.sleep(np.random.uniform(0.5, 1.5))
            elif state == 'blink':
                # Blink animation: open -> closed -> open quickly
                for _ in range(1): # A single blink cycle
                    with canvas(device) as draw_blink:
                        draw_closed_eye(draw_blink, center_x + LEFT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y)
                        draw_closed_eye(draw_blink, center_x + RIGHT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y)
                    time.sleep(0.1) # Short delay for closed state
                    with canvas(device) as draw_open:
                        draw_anime_eye(draw_open, center_x + LEFT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, highlight_pos=highlight_choice)
                        draw_anime_eye(draw_open, center_x + RIGHT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, highlight_pos=highlight_choice)
                    time.sleep(0.1) # Short delay after opening
                time.sleep(np.random.uniform(0.5, 1.0)) # Pause after the blink sequence
            elif state == 'happy':
                draw_happy_eyes(draw, highlight_pos=highlight_choice)
                time.sleep(np.random.uniform(1.0, 2.5))
            elif state == 'sad':
                draw_sad_eyes(draw, highlight_pos=highlight_choice)
                time.sleep(np.random.uniform(1.0, 2.5))
            elif state == 'surprised':
                draw_surprised_eyes(draw)
                time.sleep(np.random.uniform(0.7, 1.5))
                # Return to a normal state after a brief surprise
                with canvas(device) as draw_norm:
                    draw_anime_eye(draw_norm, center_x + LEFT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, highlight_pos=highlight_choice)
                    draw_anime_eye(draw_norm, center_x + RIGHT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, highlight_pos=highlight_choice)
                time.sleep(0.5)
            elif state == 'wink_left':
                draw_wink_eyes(draw, left_wink=True)
                time.sleep(np.random.uniform(0.7, 1.5))
                # Return to normal after wink
                with canvas(device) as draw_norm:
                    draw_anime_eye(draw_norm, center_x + LEFT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, highlight_pos=highlight_choice)
                    draw_anime_eye(draw_norm, center_x + RIGHT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, highlight_pos=highlight_choice)
                time.sleep(0.5)
            elif state == 'wink_right':
                draw_wink_eyes(draw, left_wink=False)
                time.sleep(np.random.uniform(0.7, 1.5))
                # Return to normal after wink
                with canvas(device) as draw_norm:
                    draw_anime_eye(draw_norm, center_x + LEFT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, highlight_pos=highlight_choice)
                    draw_anime_eye(draw_norm, center_x + RIGHT_EYE_OFFSET_X, center_y + EYE_OFFSET_Y, highlight_pos=highlight_choice)
                time.sleep(0.5)
            elif state == 'sleepy':
                draw_sleepy_eyes(draw)
                time.sleep(np.random.uniform(1.5, 3.0)) # Stay sleepy for longer

# --- Main execution block ---
# This block handles the starting of the animation and ensures proper cleanup
# if the script is interrupted or finishes.
try:
    # Clear the display initially to ensure a clean start
    # Check if 'device' was successfully initialized before attempting to clear.
    if 'device' in locals() and device:
        device.clear()
        print("Starting cute anime eye animation...")
        animate_eyes()

except KeyboardInterrupt:
    # This block executes if the user presses Ctrl+C to stop the script
    print("\nKeyboardInterrupt detected. Exiting animation.")
except Exception as e:
    # Catch any other unexpected errors during execution
    print(f"\nAn unexpected error occurred: {e}")
finally:
    # This 'finally' block *always* executes, whether an exception occurred or not.
    # It's crucial for ensuring the display is cleared upon script termination.
    if 'device' in locals() and device:
        device.clear() # Send the clear command to turn off all pixels
        # Add a small delay to give the OLED controller time to process the clear command
        time.sleep(0.5)
        print("Display cleared and resources released.")
    else:
        print("Display device not initialized or already cleaned up. No further action needed.")
