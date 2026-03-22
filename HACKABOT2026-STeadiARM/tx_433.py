"""
tx_433.py  –  SteadiARM Glove Pico (Pico 1)
433 MHz FS1000A transmitter

Wiring:
    FS1000A VCC  → 3.3V
    FS1000A GND  → GND
    FS1000A DATA → GP2
    Antenna      → 17 cm wire soldered to ANT pad
"""

from machine import Pin
import utime
import struct

# ── config ────────────────────────────────────────────────────────────────────
TX_PIN    = 8
BIT_US    = 2000   # 2 ms per bit → 500 bit/s (slow = reliable over 433 MHz)
PREAMBLE  = 12     # number of 0xAA sync bytes

tx = Pin(TX_PIN, Pin.OUT, value=0)

# ── low‑level bit/byte transmit ───────────────────────────────────────────────

def _send_bit(b):
    tx.value(b)
    utime.sleep_us(BIT_US)

def _send_byte(val):
    _send_bit(0)                          # start bit
    for i in range(8):
        _send_bit((val >> i) & 1)         # LSB first
    _send_bit(1)                          # stop bit

# ── packet framing ────────────────────────────────────────────────────────────
# Frame: [0xAA x PREAMBLE] [0x55 header] [len 1B] [payload] [checksum 1B]

def send_packet(data: bytes):
    for _ in range(PREAMBLE):
        _send_byte(0xAA)
    _send_byte(0x55)
    _send_byte(len(data))
    csum = 0
    for b in data:
        _send_byte(b)
        csum = (csum + b) & 0xFF
    _send_byte(csum)

# ── telemetry packet builder ──────────────────────────────────────────────────
# Packet layout (9 bytes):
#   f_tremor   : float32  (4 B)
#   magnitude  : float32  (4 B)  -- actually sent as uint16 × 0.0001 to save space
#   axis       : uint8    (1 B)  high nibble = axis (0/1/2), low nibble = sign (0=+,1=-)
#   motor_id   : uint8    (1 B)
#   f_motor    : uint16   (2 B)  Hz × 100
#   k_factor   : uint8    (1 B)  k × 10  (range 0.1 – 25.5)
#   mode       : uint8    (1 B)  0=normal, 1=calibration
# Total payload = 11 bytes

PACKET_FMT = ">HHBBHBB"   # big-endian

def build_telemetry(f_tremor, magnitude, axis, axis_sign,
                    motor_id, f_motor, k_factor, mode):
    ft   = int(f_tremor  * 100) & 0xFFFF
    mag  = int(magnitude * 100) & 0xFFFF
    ax   = ((axis & 0x0F) << 4) | (0 if axis_sign >= 0 else 1)
    fm   = int(f_motor   * 100) & 0xFFFF
    k    = int(k_factor  * 10)  & 0xFF
    m    = int(mode)             & 0xFF
    return struct.pack(PACKET_FMT, ft, mag, ax, motor_id, fm, k, m)

# ── demo loop (replace with real IMU values) ──────────────────────────────────

if __name__ == "__main__":
    print("TX 433 MHz – SteadiARM glove Pico")
    seq = 0
    while True:
        # TODO: replace these with real values from TremorDetector
        pkt = build_telemetry(
            f_tremor  = 5.0,    # Hz
            magnitude = 0.12,   # m/s²
            axis      = 0,      # X axis
            axis_sign = 1,      # positive
            motor_id  = 1,
            f_motor   = 15.0,   # Hz
            k_factor  = 3.0,
            mode      = 0       # normal
        )
        send_packet(pkt)
        seq += 1
        print(f"TX packet #{seq}  ({len(pkt)} B payload)")
        utime.sleep_ms(100)     # ~10 Hz telemetry rate
