import time
import random
from luma.core.interface.serial import spi
from luma.oled.device import ssd1306
from PIL import ImageDraw, Image

# --- Configuration for SPI ---
SPI_BUS = 0
SPI_DEVICE = 0  # CE0 (GPIO 8)
DC_PIN = 23     # GPIO 23 (Physical Pin 16)
RST_PIN = 24    # GPIO 24 (Physical Pin 18)

# --- OLED Device Initialization ---
oled_device = None
try:
    serial = spi(port=SPI_BUS, device=SPI_DEVICE, gpio_DC=DC_PIN, gpio_RST=RST_PIN)
    oled_device = ssd1306(serial, rotate=0)  # Added rotate=0 for proper orientation
    print(f"OLED display initialized: {oled_device.width}x{oled_device.height}")
except Exception as e:
    print(f"Error initializing OLED device: {e}")
    print("Please check wiring and luma.oled library installation.")
    exit()

# --- Display Colors ---
BGCOLOR = 0  # Black
MAINCOLOR = 1  # White

# --- Mood Types ---
DEFAULT = 0
TIRED = 1
ANGRY = 2
HAPPY = 3

# --- Predefined Positions ---
N = 1  # North
NE = 2
E = 3
SE = 4
S = 5
SW = 6
W = 7
NW = 8

class RoboEyes:
    def __init__(self, display_device):
        self.device = display_device
        self.screenWidth = self.device.width
        self.screenHeight = self.device.height
        self.frameInterval = 20  # 50 FPS default
        self.fpsTimer = 0
        
        # Eye state variables
        self.tired = self.angry = self.happy = False
        self.curious = self.cyclops = False
        self.eyeL_open = self.eyeR_open = False
        
        # Left eye geometry
        self.eyeLwidthDefault = self.eyeLwidthCurrent = self.eyeLwidthNext = 36
        self.eyeLheightDefault = 36
        self.eyeLheightCurrent = 1  # Start closed
        self.eyeLheightNext = self.eyeLheightDefault
        self.eyeLheightOffset = 0
        self.eyeLborderRadiusDefault = self.eyeLborderRadiusCurrent = self.eyeLborderRadiusNext = 8
        
        # Right eye geometry
        self.eyeRwidthDefault = self.eyeRwidthCurrent = self.eyeRwidthNext = 36
        self.eyeRheightDefault = 36
        self.eyeRheightCurrent = 1  # Start closed
        self.eyeRheightNext = self.eyeRheightDefault
        self.eyeRheightOffset = 0
        self.eyeRborderRadiusDefault = self.eyeRborderRadiusCurrent = self.eyeRborderRadiusNext = 8
        
        # Eye positions
        self.spaceBetweenDefault = 10
        self.eyeLxDefault = ((self.screenWidth) - (36 + 10 + 36)) // 2
        self.eyeLyDefault = (self.screenHeight - 36) // 2
        self.eyeLx = self.eyeLxNext = self.eyeLxDefault
        self.eyeLy = self.eyeLyNext = self.eyeLyDefault
        self.eyeRxDefault = self.eyeLx + 36 + 10
        self.eyeRyDefault = self.eyeLy
        self.eyeRx = self.eyeRxNext = self.eyeRxDefault
        self.eyeRy = self.eyeRyNext = self.eyeRyDefault
        
        # Eyelids
        self.eyelidsHeightMax = 18
        self.eyelidsTiredHeight = self.eyelidsTiredHeightNext = 0
        self.eyelidsAngryHeight = self.eyelidsAngryHeightNext = 0
        self.eyelidsHappyBottomOffsetMax = 21
        self.eyelidsHappyBottomOffset = self.eyelidsHappyBottomOffsetNext = 0
        self.spaceBetweenCurrent = self.spaceBetweenNext = 10
        
        # Animation controls
        self.hFlicker = self.vFlicker = False
        self.hFlickerAlternate = self.vFlickerAlternate = False
        self.hFlickerAmplitude = 2
        self.vFlickerAmplitude = 10
        
        self.autoblinker = False
        self.blinkInterval = 1
        self.blinkIntervalVariation = 4
        self.blinktimer = 0
        
        self.idle = False
        self.idleInterval = 1
        self.idleIntervalVariation = 3
        self.idleAnimationTimer = 0
        
        self.confused = False
        self.confusedAnimationTimer = 0
        self.confusedAnimationDuration = 500
        self.confusedToggle = True
        
        self.laugh = False
        self.laughAnimationTimer = 0
        self.laughAnimationDuration = 500
        self.laughToggle = True

    def begin(self, width, height, frameRate):
        """Initialize display with given dimensions and framerate."""
        self.screenWidth = width
        self.screenHeight = height
        
        # Clear display with blank image
        blank = Image.new('1', (width, height), BGCOLOR)
        self.device.display(blank)
        
        self.eyeLheightCurrent = 1  # Start with closed eyes
        self.eyeRheightCurrent = 1
        self.setFramerate(frameRate)
        
        # Recalculate positions
        self.eyeLxDefault = ((width) - (36 + 10 + 36)) // 2
        self.eyeLyDefault = (height - 36) // 2
        self.eyeLx = self.eyeLxNext = self.eyeLxDefault
        self.eyeLy = self.eyeLyNext = self.eyeLyDefault
        self.eyeRxDefault = self.eyeLx + 36 + 10
        self.eyeRyDefault = self.eyeLy
        self.eyeRx = self.eyeRxNext = self.eyeRxDefault
        self.eyeRy = self.eyeRyNext = self.eyeRyDefault

    def update(self):
        """Update display at configured framerate."""
        current_time_ms = time.monotonic_ns() // 1_000_000
        if current_time_ms - self.fpsTimer >= self.frameInterval:
            self.drawEyes()
            self.fpsTimer = current_time_ms

    # --- Setters ---
    def setFramerate(self, fps):
        self.frameInterval = 1000 // max(1, fps)  # Prevent division by zero

    def setWidth(self, leftEye, rightEye):
        self.eyeLwidthNext = self.eyeLwidthDefault = leftEye
        self.eyeRwidthNext = self.eyeRwidthDefault = rightEye

    def setHeight(self, leftEye, rightEye):
        self.eyeLheightNext = self.eyeLheightDefault = leftEye
        self.eyeRheightNext = self.eyeRheightDefault = rightEye

    def setBorderradius(self, leftEye, rightEye):
        self.eyeLborderRadiusNext = self.eyeLborderRadiusDefault = leftEye
        self.eyeRborderRadiusNext = self.eyeRborderRadiusDefault = rightEye

    def setSpacebetween(self, space):
        self.spaceBetweenNext = self.spaceBetweenDefault = space

    def setMood(self, mood):
        self.tired = self.angry = self.happy = False
        if mood == TIRED: self.tired = True
        elif mood == ANGRY: self.angry = True
        elif mood == HAPPY: self.happy = True

    def setPosition(self, position):
        if position == N:
            self.eyeLxNext, self.eyeLyNext = self.getScreenConstraint_X() // 2, 0
        elif position == NE:
            self.eyeLxNext, self.eyeLyNext = self.getScreenConstraint_X(), 0
        elif position == E:
            self.eyeLxNext, self.eyeLyNext = self.getScreenConstraint_X(), self.getScreenConstraint_Y() // 2
        elif position == SE:
            self.eyeLxNext, self.eyeLyNext = self.getScreenConstraint_X(), self.getScreenConstraint_Y()
        elif position == S:
            self.eyeLxNext, self.eyeLyNext = self.getScreenConstraint_X() // 2, self.getScreenConstraint_Y()
        elif position == SW:
            self.eyeLxNext, self.eyeLyNext = 0, self.getScreenConstraint_Y()
        elif position == W:
            self.eyeLxNext, self.eyeLyNext = 0, self.getScreenConstraint_Y() // 2
        elif position == NW:
            self.eyeLxNext, self.eyeLyNext = 0, 0
        else:  # DEFAULT
            self.eyeLxNext, self.eyeLyNext = self.getScreenConstraint_X() // 2, self.getScreenConstraint_Y() // 2

    def setAutoblinker(self, active, interval=1, variation=0):
        self.autoblinker = active
        self.blinkInterval = interval
        self.blinkIntervalVariation = variation
        if active:
            self.blinktimer = (time.monotonic_ns() // 1_000_000 + 
                             (interval * 1000) + 
                             (random.randint(0, variation) * 1000))

    def setIdleMode(self, active, interval=1, variation=0):
        self.idle = active
        self.idleInterval = interval
        self.idleIntervalVariation = variation
        if active:
            self.idleAnimationTimer = (time.monotonic_ns() // 1_000_000 + 
                                      (interval * 1000) + 
                                      (random.randint(0, variation) * 1000))

    def setCuriosity(self, curiousBit):
        self.curious = curiousBit

    def setCyclops(self, cyclopsBit):
        self.cyclops = cyclopsBit

    def setHFlicker(self, flickerBit, amplitude=2):
        self.hFlicker = flickerBit
        self.hFlickerAmplitude = amplitude

    def setVFlicker(self, flickerBit, amplitude=10):
        self.vFlicker = flickerBit
        self.vFlickerAmplitude = amplitude

    # --- Getters ---
    def getScreenConstraint_X(self):
        return self.screenWidth - self.eyeLwidthCurrent - self.spaceBetweenCurrent - self.eyeRwidthCurrent

    def getScreenConstraint_Y(self):
        return self.screenHeight - self.eyeLheightDefault

    # --- Eye Control ---
    def close(self, left=True, right=True):
        if left:
            self.eyeLheightNext = 1
            self.eyeL_open = False
        if right:
            self.eyeRheightNext = 1
            self.eyeR_open = False

    def open(self, left=True, right=True):
        if left:
            self.eyeL_open = True
            self.eyeLheightNext = self.eyeLheightDefault
        if right:
            self.eyeR_open = True
            self.eyeRheightNext = self.eyeRheightDefault

    def blink(self, left=True, right=True):
        self.close(left, right)

    # --- Animations ---
    def anim_confused(self):
        self.confused = True
        self.confusedToggle = True

    def anim_laugh(self):
        self.laugh = True
        self.laughToggle = True

    def drawEyes(self):
        current_time_ms = time.monotonic_ns() // 1_000_000

        # --- Pre-calculations ---
        # Handle curious gaze
        if self.curious:
            self.eyeLheightOffset = 8 if (self.eyeLxNext <= 10 or 
                (self.cyclops and self.eyeLxNext >= (self.getScreenConstraint_X() - 10))) else 0
            self.eyeRheightOffset = 8 if self.eyeRxNext >= self.screenWidth - self.eyeRwidthCurrent - 10 else 0
        else:
            self.eyeLheightOffset = self.eyeRheightOffset = 0

        # Tween eye heights
        self.eyeLheightCurrent = (self.eyeLheightCurrent + self.eyeLheightNext + self.eyeLheightOffset) // 2
        self.eyeLy += (self.eyeLheightDefault - self.eyeLheightCurrent) // 2 - self.eyeLheightOffset // 2
        
        self.eyeRheightCurrent = (self.eyeRheightCurrent + self.eyeRheightNext + self.eyeRheightOffset) // 2
        self.eyeRy += (self.eyeRheightDefault - self.eyeRheightCurrent) // 2 - self.eyeRheightOffset // 2

        # Handle eye opening
        if self.eyeL_open and self.eyeLheightCurrent <= 1 + self.eyeLheightOffset:
            self.eyeLheightNext = self.eyeLheightDefault
        if self.eyeR_open and self.eyeRheightCurrent <= 1 + self.eyeRheightOffset:
            self.eyeRheightNext = self.eyeRheightDefault

        # Tween other properties
        self.eyeLwidthCurrent = (self.eyeLwidthCurrent + self.eyeLwidthNext) // 2
        self.eyeRwidthCurrent = (self.eyeRwidthCurrent + self.eyeRwidthNext) // 2
        self.spaceBetweenCurrent = (self.spaceBetweenCurrent + self.spaceBetweenNext) // 2
        
        self.eyeLx = (self.eyeLx + self.eyeLxNext) // 2
        self.eyeLy = (self.eyeLy + self.eyeLyNext) // 2
        
        self.eyeRxNext = self.eyeLxNext + self.eyeLwidthCurrent + self.spaceBetweenCurrent
        self.eyeRyNext = self.eyeLyNext
        self.eyeRx = (self.eyeRx + self.eyeRxNext) // 2
        self.eyeRy = (self.eyeRy + self.eyeRyNext) // 2
        
        self.eyeLborderRadiusCurrent = (self.eyeLborderRadiusCurrent + self.eyeLborderRadiusNext) // 2
        self.eyeRborderRadiusCurrent = (self.eyeRborderRadiusCurrent + self.eyeRborderRadiusNext) // 2

        # --- Handle animations ---
        if self.autoblinker and current_time_ms >= self.blinktimer:
            self.blink()
            self.blinktimer = (current_time_ms + 
                              (self.blinkInterval * 1000) + 
                              (random.randint(0, self.blinkIntervalVariation) * 1000)

        if self.laugh:
            if self.laughToggle:
                self.setVFlicker(True, 5)
                self.laughAnimationTimer = current_time_ms
                self.laughToggle = False
            elif current_time_ms >= self.laughAnimationTimer + self.laughAnimationDuration:
                self.setVFlicker(False)
                self.laugh = False

        if self.confused:
            if self.confusedToggle:
                self.setHFlicker(True, 20)
                self.confusedAnimationTimer = current_time_ms
                self.confusedToggle = False
            elif current_time_ms >= self.confusedAnimationTimer + self.confusedAnimationDuration:
                self.setHFlicker(False)
                self.confused = False

        if self.idle and current_time_ms >= self.idleAnimationTimer:
            self.eyeLxNext = random.randint(0, self.getScreenConstraint_X())
            self.eyeLyNext = random.randint(0, self.getScreenConstraint_Y())
            self.idleAnimationTimer = (current_time_ms + 
                                      (self.idleInterval * 1000) + 
                                      (random.randint(0, self.idleIntervalVariation) * 1000)

        # Apply flicker effects
        if self.hFlicker:
            offset = self.hFlickerAmplitude * (1 if self.hFlickerAlternate else -1)
            self.eyeLx += offset
            self.eyeRx += offset
            self.hFlickerAlternate = not self.hFlickerAlternate

        if self.vFlicker:
            offset = self.vFlickerAmplitude * (1 if self.vFlickerAlternate else -1)
            self.eyeLy += offset
            self.eyeRy += offset
            self.vFlickerAlternate = not self.vFlickerAlternate

        # Handle cyclops mode
        if self.cyclops:
            self.eyeRwidthCurrent = self.eyeRheightCurrent = self.spaceBetweenCurrent = 0

        # --- Drawing ---
        image = Image.new('1', (self.screenWidth, self.screenHeight))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, self.screenWidth, self.screenHeight), fill=BGCOLOR)

        # Draw eyes
        draw.rounded_rectangle(
            (self.eyeLx, self.eyeLy, 
             self.eyeLx + self.eyeLwidthCurrent, self.eyeLy + self.eyeLheightCurrent),
            radius=self.eyeLborderRadiusCurrent,
            fill=MAINCOLOR
        )

        if not self.cyclops:
            draw.rounded_rectangle(
                (self.eyeRx, self.eyeRy,
                 self.eyeRx + self.eyeRwidthCurrent, self.eyeRy + self.eyeRheightCurrent),
                radius=self.eyeRborderRadiusCurrent,
                fill=MAINCOLOR
            )

        # Handle mood expressions
        if self.tired:
            self.eyelidsTiredHeightNext = self.eyeLheightCurrent // 2
            self.eyelidsAngryHeightNext = 0
        else:
            self.eyelidsTiredHeightNext = 0

        if self.angry:
            self.eyelidsAngryHeightNext = self.eyeLheightCurrent // 2
            self.eyelidsTiredHeightNext = 0
        else:
            self.eyelidsAngryHeightNext = 0

        if self.happy:
            self.eyelidsHappyBottomOffsetNext = self.eyeLheightCurrent // 2
        else:
            self.eyelidsHappyBottomOffsetNext = 0

        # Draw eyelids
        self.eyelidsTiredHeight = (self.eyelidsTiredHeight + self.eyelidsTiredHeightNext) // 2
        if self.eyelidsTiredHeight > 0:
            if not self.cyclops:
                draw.polygon([(self.eyeLx, self.eyeLy), 
                            (self.eyeLx + self.eyeLwidthCurrent, self.eyeLy),
                            (self.eyeLx, self.eyeLy + self.eyelidsTiredHeight)], fill=BGCOLOR)
                draw.polygon([(self.eyeRx, self.eyeRy),
                            (self.eyeRx + self.eyeRwidthCurrent, self.eyeRy),
                            (self.eyeRx + self.eyeRwidthCurrent, self.eyeRy + self.eyelidsTiredHeight)], fill=BGCOLOR)
            else:
                draw.polygon([(self.eyeLx, self.eyeLy),
                            (self.eyeLx + (self.eyeLwidthCurrent // 2), self.eyeLy),
                            (self.eyeLx, self.eyeLy + self.eyelidsTiredHeight)], fill=BGCOLOR)
                draw.polygon([(self.eyeLx + (self.eyeLwidthCurrent // 2), self.eyeLy),
                            (self.eyeLx + self.eyeLwidthCurrent, self.eyeLy),
                            (self.eyeLx + self.eyeLwidthCurrent, self.eyeLy + self.eyelidsTiredHeight)], fill=BGCOLOR)

        self.eyelidsAngryHeight = (self.eyelidsAngryHeight + self.eyelidsAngryHeightNext) // 2
        if self.eyelidsAngryHeight > 0:
            if not self.cyclops:
                draw.polygon([(self.eyeLx, self.eyeLy),
                            (self.eyeLx + self.eyeLwidthCurrent, self.eyeLy),
                            (self.eyeLx + self.eyeLwidthCurrent, self.eyeLy + self.eyelidsAngryHeight)], fill=BGCOLOR)
                draw.polygon([(self.eyeRx, self.eyeRy),
                            (self.eyeRx + self.eyeRwidthCurrent, self.eyeRy),
                            (self.eyeRx, self.eyeRy + self.eyelidsAngryHeight)], fill=BGCOLOR)
            else:
                draw.polygon([(self.eyeLx, self.eyeLy),
                            (self.eyeLx + (self.eyeLwidthCurrent // 2), self.eyeLy),
                            (self.eyeLx + (self.eyeLwidthCurrent // 2), self.eyeLy + self.eyelidsAngryHeight)], fill=BGCOLOR)
                draw.polygon([(self.eyeLx + (self.eyeLwidthCurrent // 2), self.eyeLy),
                            (self.eyeLx + self.eyeLwidthCurrent, self.eyeLy),
                            (self.eyeLx + self.eyeLwidthCurrent, self.eyeLy + self.eyelidsAngryHeight)], fill=BGCOLOR)

        self.eyelidsHappyBottomOffset = (self.eyelidsHappyBottomOffset + self.eyelidsHappyBottomOffsetNext) // 2
        if self.eyelidsHappyBottomOffset > 0:
            draw.rounded_rectangle(
                (self.eyeLx - 1, (self.eyeLy + self.eyeLheightCurrent) - self.eyelidsHappyBottomOffset + 1,
                 self.eyeLx + self.eyeLwidthCurrent + 2, self.eyeLy + self.eyeLheightCurrent + self.eyeLheightDefault),
                radius=self.eyeLborderRadiusCurrent,
                fill=BGCOLOR
            )
            if not self.cyclops:
                draw.rounded_rectangle(
                    (self.eyeRx - 1, (self.eyeRy + self.eyeRheightCurrent) - self.eyelidsHappyBottomOffset + 1,
                     self.eyeRx + self.eyeRwidthCurrent + 2, self.eyeRy + self.eyeRheightCurrent + self.eyeRheightDefault),
                    radius=self.eyeRborderRadiusCurrent,
                    fill=BGCOLOR
                )

        # Display the final image
        self.device.display(image)

# --- Main Program ---
if oled_device:
    try:
        eyes = RoboEyes(oled_device)
        eyes.begin(oled_device.width, oled_device.height, 50)
        
        print("RoboEyes animation running...")
        eyes.setIdleMode(True, 2, 3)
        eyes.setAutoblinker(True, 1, 4)
        eyes.setCuriosity(True)
        
        mood_timer = time.monotonic_ns() // 1_000_000
        current_mood_idx = 0
        moods = [DEFAULT, HAPPY, ANGRY, TIRED]
        mood_names = ["DEFAULT", "HAPPY", "ANGRY", "TIRED"]
        
        while True:
            eyes.update()
            
            # Rotate moods every 5 seconds
            current_time = time.monotonic_ns() // 1_000_000
            if current_time - mood_timer >= 5000:
                current_mood_idx = (current_mood_idx + 1) % len(moods)
                eyes.setMood(moods[current_mood_idx])
                mood_timer = current_time
                print(f"Mood changed to: {mood_names[current_mood_idx]}")
            
            # Random animations
            if random.random() < 0.01:
                eyes.anim_confused()
                print("Confused animation triggered!")
            if random.random() < 0.01:
                eyes.anim_laugh()
                print("Laugh animation triggered!")
                
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
    finally:
        # Clear display on exit
        blank = Image.new('1', (oled_device.width, oled_device.height), BGCOLOR)
        oled_device.display(blank)
        print("Display cleared. Goodbye!")
else:
    print("OLED initialization failed. Cannot run animation.")
