"""
rx_433.py  –  SteadiARM Base Pico (Pico 2)
433 MHz XY‑MK‑5V receiver

Wiring:
    XY-MK-5V VCC  → 5V (NOT 3.3V)
    XY-MK-5V GND  → GND (shared with Pico)
    XY-MK-5V DATA → NPN level-shift circuit → GP3
        (receiver DATA → 10kΩ → NPN base, emitter → GND,
         collector → GP3 with 10kΩ pull-up to 3.3V)
    Antenna        → 17 cm wire on ANT pad
"""

from machine import Pin
import utime
import struct

# ── config ────────────────────────────────────────────────────────────────────
RX_PIN   = 9
BIT_US   = 2000          # must match transmitter
HALF_BIT = BIT_US // 2   # tolerance window

PACKET_FMT = ">HHBBHBB"
PAYLOAD_LEN = struct.calcsize(PACKET_FMT)   # 11 bytes

# ── shared state (written in IRQ, read in main) ───────────────────────────────
_last_us   = 0
_bits      = []
_bytes_buf = []
_packets   = []   # completed, validated packets land here

# State machine
_ST_PREAMBLE = 0
_ST_HEADER   = 1
_ST_LEN      = 2
_ST_DATA     = 3
_ST_CSUM     = 4

_state     = _ST_PREAMBLE
_rx_len    = 0
_rx_csum   = 0

# ── bit→byte accumulator ─────────────────────────────────────────────────────

def _push_bit(bit):
    _bits.append(bit)
    if len(_bits) == 10:                  # start + 8 data + stop
        sb = _bits[0]
        eb = _bits[9]
        val = 0
        for i in range(8):
            val |= (_bits[1 + i] << i)
        _bits.clear()
        if sb == 0 and eb == 1:           # valid framing
            _push_byte(val)

def _push_byte(b):
    global _state, _rx_len, _rx_csum, _bytes_buf

    if _state == _ST_PREAMBLE:
        if b == 0x55:
            _state = _ST_LEN
    elif _state == _ST_LEN:
        _rx_len  = b
        _rx_csum = 0
        _bytes_buf = []
        _state = _ST_DATA
    elif _state == _ST_DATA:
        _bytes_buf.append(b)
        _rx_csum = (_rx_csum + b) & 0xFF
        if len(_bytes_buf) >= _rx_len:
            _state = _ST_CSUM
    elif _state == _ST_CSUM:
        if b == _rx_csum and len(_bytes_buf) == PAYLOAD_LEN:
            _packets.append(bytes(_bytes_buf))
        # always reset regardless of validity
        _state = _ST_PREAMBLE
        _bits.clear()

# ── IRQ handler (integer arithmetic only) ─────────────────────────────────────

def _irq(pin):
    global _last_us
    now = utime.ticks_us()
    dt  = utime.ticks_diff(now, _last_us)
    _last_us = now

    n = (dt + HALF_BIT) // BIT_US        # round to nearest bit count
    if n < 1 or n > 20:
        return

    level = pin.value()
    for _ in range(n):
        _push_bit(level)

rx = Pin(RX_PIN, Pin.IN)
rx.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=_irq)

# ── telemetry decoder ─────────────────────────────────────────────────────────

def decode_packet(raw: bytes) -> dict:
    ft, mag, ax_byte, motor_id, fm, k, mode = struct.unpack(PACKET_FMT, raw)
    axis      = (ax_byte >> 4) & 0x0F
    axis_sign = -1 if (ax_byte & 0x01) else 1
    return {
        "f_tremor"  : ft / 100.0,
        "magnitude" : mag / 100.0,
        "axis"      : axis,
        "axis_sign" : axis_sign,
        "motor_id"  : motor_id,
        "f_motor"   : fm / 100.0,
        "k_factor"  : k  / 10.0,
        "mode"      : "calibration" if mode else "normal",
    }

# ── main loop ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("RX 433 MHz – SteadiARM base Pico\nListening...\n")
    while True:
        if _packets:
            raw = _packets.pop(0)
            try:
                d = decode_packet(raw)
                print(
                    f"f_t={d['f_tremor']:.2f}Hz  "
                    f"mag={d['magnitude']:.3f}  "
                    f"axis={'XYZ'[d['axis']]}{'+'if d['axis_sign']>0 else'-'}  "
                    f"motor={d['motor_id']}  "
                    f"f_m={d['f_motor']:.2f}Hz  "
                    f"k={d['k_factor']:.1f}  "
                    f"mode={d['mode']}"
                )
            except Exception as e:
                print("Decode error:", e)
        utime.sleep_ms(10)
