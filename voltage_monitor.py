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
import asyncio
import adafruit_ds1307
import wifi
import adafruit_ntp
import socketpool
import gc
import adafruit_requests as requests
from analogio import AnalogIn
import ssl

def convert(value):
    OldMin = 208
    OldMax = 65535
    NewMin = 0
    NewMax = 15
    return (((value - OldMin) * (NewMax - NewMin)) / (OldMax - OldMin)) + NewMin

def pr(s):
    text_area.text = s

def boo(s):
    return str(s or '').lower() in ['true', '1', 't', 'y', 'yes']

async def read_voltage():
    while True:
        # read voltage
        global voltage
        voltage = analog_in.value
        ctime = rtc.datetime
        td = "{hour:02d}:{minute:02d}\n{day}.{month}.{year}".format(hour=ctime.tm_hour, minute=ctime.tm_min, year=ctime.tm_year, month=ctime.tm_mon, day=ctime.tm_mday)
        text = td+"\n{v:2.2f}".format(v=convert(voltage))+"V´"
        pr(text)
        await asyncio.sleep(int(os.getenv('display_frequency')))

async def store_voltage():
    while True:
        ctime = rtc.datetime
        td = "{year}.{month}.{day} - {hour:02d}:{minute:02d}:{second:02d}".format(hour=ctime.tm_hour, minute=ctime.tm_min, second=ctime.tm_sec, year=ctime.tm_year, month=ctime.tm_mon, day=ctime.tm_mday)
        if (boo(os.getenv('use_sdcard'))):
            print(convert(voltage))
            with open("/sd/voltage_log.txt", "a+") as f:
                f.write("{ti} - {volt:2.2f}\r\n".format(ti=td, volt=convert(voltage)))
                f.flush()
        if boo(os.getenv('use_wifi')) and boo(os.getenv('use_influxdb')) :
            while not wifi.radio.connected:
                await asyncio.sleep(1)

            data = "voltage,location=office voltage={volt}".format(volt=convert(voltage))
            try:
                response = http_session.post(INFLUXDB_URL, headers=HEADERS, data=data)
                if response.status_code == 204:
                    print("Data sent to InfluxDB successfully!")
                    pass
                else:
                    print("Failed to send data to InfluxDB:", response.text)
                response.close()
            except Exception as e:
                print("Error sending data to InfluxDB:", e)
        await asyncio.sleep(int(os.getenv('store_frequency')))

async def wifi_connect():
    while True:
        if not wifi.radio.connected:
            pr("Connecting to\n"+ssid)
            try:
                wifi.radio.connect(ssid, psk)
                pr("WIFI connected!")
            except Exception as e:
                pr("Failed to connect:"+str(e))
                print("Failed to connect:"+str(e))
                await asyncio.sleep(10)
        else:
            await asyncio.sleep(20)


async def main():
    global pool,http_session
    asyncio.create_task(wifi_connect())
    while not wifi.radio.connected:
        await asyncio.sleep(1)
    await asyncio.sleep(2)
    if (boo(os.getenv('use_wifi'))):
        pool = socketpool.SocketPool(wifi.radio)
        ssl_context = ssl.create_default_context()
        http_session = requests.Session(pool, ssl_context)
        if (boo(os.getenv('use_ntp'))):
            ntp = adafruit_ntp.NTP(pool, tz_offset=int(os.getenv('timezone')))
            current_time_struct = ntp.datetime
            # store ntp to rtc
            rtc.datetime = current_time_struct
    asyncio.create_task(read_voltage())
    asyncio.create_task(store_voltage())
    while True:
        gc.collect()
        await asyncio.sleep(10)


ssid = os.getenv('ssid')
psk = os.getenv("psk")
INFLUXDB_URL_BASE = os.getenv('influxdb_url')
INFLUXDB_ORG = os.getenv('influxdb_org')
INFLUXDB_BUCKET = os.getenv('influxdb_bucket')
INFLUXDB_TOKEN = os.getenv('influxdb_token')

# Construct the full InfluxDB URL with org and bucket parameters
INFLUXDB_URL = f"{INFLUXDB_URL_BASE}?org={INFLUXDB_ORG}&bucket={INFLUXDB_BUCKET}"

HEADERS = {
    "Authorization": f"Token {INFLUXDB_TOKEN}",
    "Content-Type": "application/json"
}

displayio.release_displays()

# init display&rtc
i2c = busio.I2C(scl=board.GP1, sda=board.GP0, frequency=100000)
rtc = adafruit_ds1307.DS1307(i2c)
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_sh1106.SH1106(display_bus, rotation=180, width=128, height=64)
splash = displayio.Group()
display.root_group = splash
text = "Starting.."
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=8, y=15)
splash.append(text_area)

# init sdcard
SD_CS = board.GP17
spi = busio.SPI(board.GP18, board.GP19, board.GP16)
cs = digitalio.DigitalInOut(SD_CS)
sdcard = adafruit_sdcard.SDCard(spi, cs)
if (boo(os.getenv('use_sdcard'))):
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")

analog_in = AnalogIn(board.GP26)
voltage = 0.0

asyncio.run(main())
