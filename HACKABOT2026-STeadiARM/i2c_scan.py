"""
i2c_scan.py  –  Scan all common Pico I2C pin pairs and report found devices.
Upload and run this to find your BMI160's address and which pins it's on.
"""

from machine import I2C, Pin
import time

# All valid I2C0 and I2C1 SDA/SCL pin pairs on the Pico 2
PAIRS = [
    (0,  "I2C0", 0,  1),   # SDA=GP0,  SCL=GP1
    (0,  "I2C0", 4,  5),   # SDA=GP4,  SCL=GP5
    (0,  "I2C0", 8,  9),   # SDA=GP8,  SCL=GP9
    (0,  "I2C0", 12, 13),  # SDA=GP12, SCL=GP13
    (0,  "I2C0", 16, 17),  # SDA=GP16, SCL=GP17
    (0,  "I2C0", 20, 21),  # SDA=GP20, SCL=GP21
    (1,  "I2C1", 2,  3),   # SDA=GP2,  SCL=GP3
    (1,  "I2C1", 6,  7),   # SDA=GP6,  SCL=GP7
    (1,  "I2C1", 10, 11),  # SDA=GP10, SCL=GP11
    (1,  "I2C1", 14, 15),  # SDA=GP14, SCL=GP15
    (1,  "I2C1", 18, 19),  # SDA=GP18, SCL=GP19
    (1,  "I2C1", 26, 27),  # SDA=GP26, SCL=GP27
]

print("Scanning all I2C pin pairs...\n")

found_any = False

for bus_id, bus_name, sda_pin, scl_pin in PAIRS:
    try:
        i2c = I2C(bus_id, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=100_000)
        devices = i2c.scan()
        if devices:
            found_any = True
            for addr in devices:
                name = "BMI160" if addr in (0x68, 0x69) else "unknown"
                print(f"  FOUND  {bus_name}  SDA=GP{sda_pin}  SCL=GP{scl_pin}"
                      f"  addr=0x{addr:02X}  ({name})")
    except Exception:
        pass   # pin pair not usable, skip

if not found_any:
    print("  No I2C devices found on any pin pair.")
    print("\n  Check:")
    print("    1. VCC connected to 3.3V (NOT 5V)")
    print("    2. GND connected")
    print("    3. SDA and SCL not swapped")
    print("    4. SDO pin connected to GND or 3.3V (not floating)")
else:
    print("\nUpdate the I2C() call in main.py to match the pin pair shown above.")
