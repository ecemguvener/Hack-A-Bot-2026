"""
===========================================================================
receiver.py  -  SteadiARM Base Pico (Pico 2 / RP2350)
===========================================================================
PURPOSE:
    Runs on the BASE Pico (Pi #2). Acts as the bridge between the glove
    and the PC/operator.

    1. Receives telemetry from the glove Pico via 433 MHz RF (XY-MK-5V).
    2. Decodes and prints each packet to USB serial for the PC to read/plot.
    3. Reads config commands typed on the PC via USB serial (plain text).
    4. Encodes and transmits config packets back to the glove (FS1000A).

HARDWARE (on this Pico):
    - 1x XY-MK-5V 433 MHz receiver  (needs 3.3 V level-shifter on DATA)
    - 1x FS1000A  433 MHz transmitter
    - USB connection to PC (for telemetry output + config input)

PC -> BASE PICO COMMANDS  (type into the serial terminal and press Enter):
    k=<value>       Set k_factor               e.g.  k=3.5
    mode=<0..3>     Set mode                   e.g.  mode=2
                    0=normal closed-loop
                    1=calibration
                    2=continuous ON (latched vibration until OFF)
                    3=OFF (motors forced off)
    on              Shortcut for mode=2
    off             Shortcut for mode=3
    limit=<value>   Set intensity limit        e.g.  limit=0.8
    status          Print current config
===========================================================================
"""

# ===========================================================================
# STEP 0 - IMPORTS
# ===========================================================================
from machine import Pin
import utime
import time
import struct
import sys


# ===========================================================================
# STEP 1 - PIN CONFIGURATION
# ---------------------------------------------------------------------------
# EDIT THE NUMBERS BELOW before plugging everything in.
# All numbers are GPIO numbers (GPxx on the Pico 2 pinout diagram).
# ===========================================================================

# ---- 433 MHz Receiver (XY-MK-5V) - receives telemetry from glove ----
# IMPORTANT: XY-MK-5V DATA outputs 5 V. Use an NPN level-shifter:
#   DATA -> 10k -> NPN base | NPN emitter -> GND
#   NPN collector -> GP0 with 10k pull-up to 3.3V
RX_PIN = 0     # GP0  -> XY-MK-5V DATA (after level-shift to 3.3 V)

# ---- 433 MHz Transmitter (FS1000A) - sends config back to glove ----
TX_PIN = 2     # GP2  -> FS1000A DATA pin
               # FS1000A VCC -> 3.3V,  GND -> GND

# ---- Status LED ----
LED_PIN = 25   # GP25 -> Pico 2 onboard LED


# ===========================================================================
# STEP 2 - 433 MHz RECEIVER  (interrupt-driven, decodes telemetry packets)
# ---------------------------------------------------------------------------
# Telemetry packet layout (11 bytes, big-endian) - must match final_proj.py:
#   f_tremor   uint16  Hz x 100
#   magnitude  uint16  m/s^2 x 100
#   axis_byte  uint8   high nibble=axis(0/1/2), low bit=sign(0=+, 1=-)
#   motor_id   uint8   0-3
#   f_motor    uint16  Hz x 100
#   k_factor   uint8   k x 10
#   mode       uint8   0=normal, 1=calibration, 2=continuous_on, 3=off
# ===========================================================================

_RX_BIT_US   = 2000              # must match final_proj.py TX settings
_HALF_BIT    = _RX_BIT_US // 2
_TELEM_FMT   = ">HHBBHBB"
_TELEM_LEN   = struct.calcsize(_TELEM_FMT)   # 11 bytes

# ---- Receiver state (written in IRQ, read in main loop) ----
_rx_last_us  = 0
_rx_bits     = []
_rx_buf      = []
_rx_packets  = []    # fully decoded, validated telemetry payloads land here

_ST_PREAMBLE = 0
_ST_LEN      = 1
_ST_DATA     = 2
_ST_CSUM     = 3

_rx_state    = _ST_PREAMBLE
_rx_len      = 0
_rx_csum_acc = 0


def _rx_push_bit(bit):
    """Accumulate bits until we have a full 10-bit UART frame (start+8+stop)."""
    global _rx_bits
    _rx_bits.append(bit)
    if len(_rx_bits) == 10:
        start = _rx_bits[0]
        stop  = _rx_bits[9]
        val   = 0
        for i in range(8):
            val |= (_rx_bits[1 + i] << i)
        _rx_bits = []
        if start == 0 and stop == 1:       # valid UART framing
            _rx_push_byte(val)


def _rx_push_byte(b):
    """State machine: assemble bytes into a validated telemetry packet."""
    global _rx_state, _rx_len, _rx_csum_acc, _rx_buf, _rx_bits

    if _rx_state == _ST_PREAMBLE:
        if b == 0x55:                      # packet start marker found
            _rx_state = _ST_LEN

    elif _rx_state == _ST_LEN:
        _rx_len      = b
        _rx_csum_acc = 0
        _rx_buf      = []
        _rx_state    = _ST_DATA

    elif _rx_state == _ST_DATA:
        _rx_buf.append(b)
        _rx_csum_acc = (_rx_csum_acc + b) & 0xFF
        if len(_rx_buf) >= _rx_len:
            _rx_state = _ST_CSUM

    elif _rx_state == _ST_CSUM:
        if b == _rx_csum_acc and len(_rx_buf) == _TELEM_LEN:
            _rx_packets.append(bytes(_rx_buf))   # valid telemetry packet
        _rx_state = _ST_PREAMBLE
        _rx_bits  = []


def _rx_irq(pin):
    """Pin IRQ handler - fires on every rising/falling edge of the RX signal."""
    global _rx_last_us
    now = utime.ticks_us()
    dt  = utime.ticks_diff(now, _rx_last_us)
    _rx_last_us = now

    n = (dt + _HALF_BIT) // _RX_BIT_US    # number of bit periods that elapsed
    if n < 1 or n > 20:
        return                              # out of range - discard noise

    level = pin.value()
    for _ in range(n):
        _rx_push_bit(level)


def decode_telemetry(raw: bytes) -> dict:
    """
    Decode an 11-byte telemetry payload into a human-readable dict.
    Inverse of build_telemetry_packet() in final_proj.py.
    """
    ft, mag, ax_byte, motor_id, fm, k, mode = struct.unpack(_TELEM_FMT, raw)
    axis      = (ax_byte >> 4) & 0x0F
    axis_sign = -1 if (ax_byte & 0x01) else 1
    mode_label = ("normal", "calibration", "continuous_on", "off")
    mode_str = mode_label[mode] if 0 <= mode < len(mode_label) else f"mode{mode}"
    return {
        "f_tremor"  : ft  / 100.0,
        "magnitude" : mag / 100.0,
        "axis"      : axis,
        "axis_sign" : axis_sign,
        "motor_id"  : motor_id,
        "f_motor"   : fm  / 100.0,
        "k_factor"  : k   / 10.0,
        "mode"      : mode_str,
    }


# ===========================================================================
# STEP 3 - 433 MHz TRANSMITTER  (FS1000A, base -> glove config packets)
# ---------------------------------------------------------------------------
# Config payload (3 bytes, big-endian) - must match receiver in final_proj.py:
#   mode            uint8   0=normal, 1=calibration, 2=continuous_on, 3=off
#   k_factor        uint8   k x 10        (e.g. 30 -> k=3.0)
#   intensity_limit uint8   limit x 100   (e.g. 80 -> 0.80)
# ===========================================================================

_TX_BIT_US   = 2000
_TX_PREAMBLE = 12
_CFG_FMT     = ">BBB"


def _tx_bit(pin, b):
    pin.value(b)
    utime.sleep_us(_TX_BIT_US)


def _tx_byte(pin, val):
    _tx_bit(pin, 0)                        # start bit
    for i in range(8):
        _tx_bit(pin, (val >> i) & 1)       # 8 data bits, LSB first
    _tx_bit(pin, 1)                        # stop bit


def rf_send_config(tx_pin, mode, k_factor, intensity_limit):
    """
    Encode and transmit a config packet to the glove Pico.
    Called whenever the PC sends a new config command.

    Args:
        tx_pin          : machine.Pin in output mode
        mode            : 0=normal, 1=calibration, 2=continuous_on, 3=off
        k_factor        : frequency multiplier (e.g. 3.0)
        intensity_limit : motor intensity cap  (0.0 - 1.0)
    """
    # Encode floats to compact integer fields
    k_raw   = int(k_factor        * 10)  & 0xFF
    lim_raw = int(intensity_limit * 100) & 0xFF
    payload = struct.pack(_CFG_FMT, int(mode), k_raw, lim_raw)

    # Transmit using the same frame format as final_proj.py
    for _ in range(_TX_PREAMBLE):
        _tx_byte(tx_pin, 0xAA)            # sync preamble
    _tx_byte(tx_pin, 0x55)                # packet start marker
    _tx_byte(tx_pin, len(payload))        # payload length byte

    csum = 0
    for b in payload:
        _tx_byte(tx_pin, b)
        csum = (csum + b) & 0xFF
    _tx_byte(tx_pin, csum)                # checksum

    print(f"[TX->GLOVE] mode={mode}  k={k_factor:.1f}  limit={intensity_limit:.2f}")


# ===========================================================================
# STEP 4 - PC COMMAND PARSER  (USB serial input)
# ---------------------------------------------------------------------------
# The PC operator types plain-text commands into the serial terminal.
# Each command is one line.  Format:  key=value  (no spaces around =)
#
# Supported commands:
#   k=<float>      update k_factor          e.g.  k=4.2
#   mode=<0..3>    switch mode              e.g.  mode=2
#   on / off       quick continuous ON / OFF
#   limit=<float>  update intensity limit   e.g.  limit=0.75
#   status         print current config
# ===========================================================================

_MODE_LABEL = {
    0: "normal",
    1: "calibration",
    2: "continuous_on",
    3: "off",
}

def parse_pc_command(line: str, cfg: dict):
    """
    Parse one text command from the PC.
    Modifies cfg in-place if valid, returns True if a change was made.
    Returns False for unknown or malformed commands.
    """
    line = line.strip()

    if line == "status":
        print(f"[STATUS] mode={cfg['mode']}({_MODE_LABEL.get(cfg['mode'], cfg['mode'])})  "
              f"k={cfg['k_factor']:.1f}  "
              f"limit={cfg['intensity_limit']:.2f}")
        return False   # status request - no config change to send

    if "=" not in line:
        if line.lower() == "on":
            cfg["mode"] = 2
            print("[CMD] mode set to continuous_on")
            return True
        if line.lower() == "off":
            cfg["mode"] = 3
            print("[CMD] mode set to off")
            return True
        if line:
            print(f"[CMD?] Unknown: '{line}'  "
                  "Try: k=3.5  mode=2  on  off  limit=0.8  status")
        return False

    key, _, val = line.partition("=")
    key = key.strip().lower()
    val = val.strip()

    try:
        if key == "k":
            v = float(val)
            if not (0.1 <= v <= 25.0):
                print(f"[CMD ERR] k must be 0.1-25.0, got {v}")
                return False
            cfg["k_factor"] = v
            print(f"[CMD] k_factor set to {v:.1f}")

        elif key == "mode":
            v = int(val)
            if v not in (0, 1, 2, 3):
                print(f"[CMD ERR] mode must be 0..3, got {v}")
                return False
            cfg["mode"] = v
            print(f"[CMD] mode set to {_MODE_LABEL.get(v, v)}")

        elif key == "limit":
            v = float(val)
            if not (0.0 <= v <= 1.0):
                print(f"[CMD ERR] limit must be 0.0-1.0, got {v}")
                return False
            cfg["intensity_limit"] = v
            print(f"[CMD] intensity_limit set to {v:.2f}")

        else:
            print(f"[CMD?] Unknown key '{key}'.  Try: k=  mode=  on/off  limit=  status")
            return False

        return True   # a valid change was made -> caller should send to glove

    except ValueError:
        print(f"[CMD ERR] Bad value in '{line}'")
        return False


# ===========================================================================
# STEP 5 - MAIN LOOP
# ---------------------------------------------------------------------------
# Polls for:
#   - New RF telemetry packets from the glove -> decode and print to USB
#   - New text commands from the PC via USB serial -> parse and relay to glove
# ===========================================================================

# Helper lookup tables for pretty-printing
_AXIS_LABELS  = ["X", "Y", "Z"]
_MOTOR_LABELS = ["DORSAL", "VOLAR", "RADIAL", "ULNAR"]

print("=" * 55)
print("  SteadiARM Base Pico - Startup")
print("=" * 55)

# Initialise hardware
led    = Pin(LED_PIN, Pin.OUT)
tx_pin = Pin(TX_PIN,  Pin.OUT, value=0)
rx_pin = Pin(RX_PIN,  Pin.IN)
rx_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=_rx_irq)

print(f"[OK] RF RX listening on GP{RX_PIN}")
print(f"[OK] RF TX ready     on GP{TX_PIN}")

# Config state - operator changes these via serial, then they're sent to glove
current_cfg = {
    "mode"            : 0,    # 0=normal, 1=calibration, 2=continuous_on, 3=off
    "k_factor"        : 3.0,  # initial k (overridden by operator at runtime)
    "intensity_limit" : 1.0,  # initial intensity cap
}

# Flag: send initial config to glove shortly after startup
config_pending  = True
startup_delay   = 3000   # ms - wait before first TX (let RF link settle)
startup_at      = time.ticks_ms()

packet_count = 0

print()
print("Waiting for telemetry from glove Pico...")
print("Commands: k=<val>  mode=<0..3>  on  off  limit=<val>  status")
print()

try:
    while True:

        # ---- Check for new RF telemetry packets from glove ----
        if _rx_packets:
            raw = _rx_packets.pop(0)
            try:
                d = decode_telemetry(raw)
                packet_count += 1

                axis_str  = _AXIS_LABELS[d["axis"]] + ("+" if d["axis_sign"] > 0 else "-")
                motor_str = (_MOTOR_LABELS[d["motor_id"]]
                             if d["motor_id"] < 4 else str(d["motor_id"]))

                # Print one line per packet - format is easy to parse on PC
                # PC can split on "|" and use the key=value fields for plotting
                print(
                    f"PKT {packet_count:05d} | "
                    f"f_tremor={d['f_tremor']:5.2f}Hz | "
                    f"magnitude={d['magnitude']:6.3f} | "
                    f"axis={axis_str} | "
                    f"motor={motor_str} | "
                    f"f_motor={d['f_motor']:5.2f}Hz | "
                    f"k={d['k_factor']:.1f} | "
                    f"mode={d['mode']}"
                )

                led.toggle()   # blink LED on each received packet

            except Exception as e:
                print(f"[DECODE ERR] {e}")

        # ---- Check for config commands from PC over USB serial ----
        try:
            import select
            if select.select([sys.stdin], [], [], 0)[0]:
                line = sys.stdin.readline()
                changed = parse_pc_command(line, current_cfg)
                if changed:
                    config_pending = True
        except ImportError:
            pass   # select not available on this build - skip

        # ---- Send initial config to glove after startup delay ----
        if config_pending:
            if time.ticks_diff(time.ticks_ms(), startup_at) >= startup_delay:
                rf_send_config(
                    tx_pin,
                    mode            = current_cfg["mode"],
                    k_factor        = current_cfg["k_factor"],
                    intensity_limit = current_cfg["intensity_limit"],
                )
                config_pending = False

        utime.sleep_ms(10)   # ~100 Hz polling rate

except KeyboardInterrupt:
    led.value(0)
    print("\n[STOP] Base Pico stopped cleanly.")
