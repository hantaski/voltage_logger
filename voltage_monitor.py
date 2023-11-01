import board
import busio
import displayio
import terminalio
import adafruit_displayio_sh1106
from adafruit_display_text import label
import time
import os
import adafruit_sdcard
import digitalio
import storage
import json
from analogio import AnalogIn


def init_sd():
    # Use any pin that is not taken by SPI
    SD_CS = board.GP17

    # Connect to the card and mount the filesystem.
    spi = busio.SPI(board.GP18, board.GP19, board.GP16)
    cs = digitalio.DigitalInOut(SD_CS)
    sdcard = adafruit_sdcard.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")


def init_display():
    global splash
    displayio.release_displays()
    i2c = busio.I2C (scl=board.GP1, sda=board.GP0, frequency=100000) # This RPi Pico way to call I2C
    display_bus = displayio.I2CDisplay (i2c, device_address = 0x3C) # The address of my Board
    display = adafruit_displayio_sh1106.SH1106(display_bus, width=128, height=64)
    splash = displayio.Group()
    display.show(splash)
    color_bitmap = displayio.Bitmap(128, 64, 1) # Full screen white
    color_palette = displayio.Palette(1)
    color_palette[0] = 0xFFFFFF  # White

    bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
    splash.append(bg_sprite)

    # Draw a smaller inner rectangle
    inner_bitmap = displayio.Bitmap(118, 54, 1)
    inner_palette = displayio.Palette(1)
    inner_palette[0] = 0x000000  # Black
    inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=5, y=4)
    splash.append(inner_sprite)

def convert(value):
    OldMin = 208
    OldMax = 65535
    NewMin = 0
    NewMax = 3.3
    return (((value - OldMin) * (NewMax - NewMin)) / (OldMax - OldMin)) + NewMin


init_display()
init_sd()
analog_in = AnalogIn(board.GP26)

# Draw a label
text = "Heippadeippa"
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=28, y=15)
splash.append(text_area)

#file = open("/sd/config.json")
#file = open("/config.json")
#data = json.load(file)
poll_frequency = os.getenv('poll_frequency')
print("poll_frequency="+str(poll_frequency))


while True:
    n = analog_in.value
    print(str(n)+" = "+str(convert(n)))
    time.sleep(poll_frequency)
    pass
