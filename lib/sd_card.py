def init_sd():
    # Use any pin that is not taken by SPI
    SD_CS = board.GP17

    # Connect to the card and mount the filesystem.
    spi = busio.SPI(board.GP18, board.GP19, board.GP16)
    cs = digitalio.DigitalInOut(SD_CS)
    sdcard = adafruit_sdcard.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")

