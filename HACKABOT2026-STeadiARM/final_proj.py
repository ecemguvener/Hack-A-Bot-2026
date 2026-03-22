"""
===========================================================================
final_proj.py  -  SteadiARM Glove Pico (Pico 2 / RP2350)
===========================================================================
PURPOSE:
    Closed-loop tremor stabilisation for Parkinson's / arthritis patients.
    Runs on the GLOVE Pico (Pi #1).

    1. Reads the BMI160 IMU (accelerometer + gyroscope) at 100 Hz.
    2. Detects tremor: dominant axis, direction, frequency, magnitude.
    3. Selects the opposing motor and drives it at  f_motor = k * f_tremor.
    4. Transmits telemetry to the base Pico via 433 MHz RF (FS1000A).
    5. Receives configuration updates (k-factor, mode) from base Pico
       via 433 MHz RF (XY-MK-5V receiver).

HARDWARE (on this Pico):
    - 1x BMI160 IMU  (I2C)
    - 2x N20 DC motors driven by 1x MX1508 dual H-bridge board:
        Board  IN1/IN2 -> Motor A  (one side of the hand)
        Board  IN3/IN4 -> Motor B  (opposing side of the hand)
    - 1x FS1000A 433 MHz transmitter
    - 1x XY-MK-5V 433 MHz receiver  (needs 3.3 V level-shifter on DATA)
===========================================================================
"""

# ===========================================================================
# STEP 0 - IMPORTS
# ===========================================================================
from machine import I2C, Pin, PWM
import utime
import time
import math
import struct


# ===========================================================================
# STEP 1 - PIN CONFIGURATION
# ---------------------------------------------------------------------------
# EDIT THE NUMBERS BELOW before plugging everything in.
# All numbers are GPIO numbers (GPxx on the Pico 2 pinout diagram).
# ===========================================================================

# ---- BMI160 IMU (I2C bus 0) ----
IMU_SDA_PIN = 14        # GP14 -> BMI160 SDA
IMU_SCL_PIN = 15        # GP15 -> BMI160 SCL
IMU_I2C_BUS = 0        # I2C peripheral 0
IMU_ADDR    = 0x68     # 0x68 when SDO->GND,  0x69 when SDO->3.3V
IMU_FREQ    = 400_000  # 400 kHz fast-mode I2C

# ---- 433 MHz Transmitter (FS1000A) - glove sends telemetry to base ----
TX_PIN = 13            # GP13 -> FS1000A DATA pin
                       # FS1000A VCC -> 3.3V,  GND -> GND

# ---- 433 MHz Receiver (XY-MK-5V) - base sends config back to glove ----
# IMPORTANT: XY-MK-5V DATA is 5 V logic. Use an NPN level-shifter:
#   DATA -> 10k -> NPN base | NPN emitter -> GND
#   NPN collector -> GP11 with 10k pull-up to 3.3V
RX_PIN = 11            # GP11 -> XY-MK-5V DATA (after level-shift)

# -----------------------------------------------------------------------
# MOTOR DRIVER BOARD  (1x MX1508 dual H-bridge)
# The MX1508 has 4 input pins that drive 2 independent motor channels:
#   IN1 + IN2  ->  Channel A  (Motor A)
#   IN3 + IN4  ->  Channel B  (Motor B)
# Mount Motor A and Motor B on opposing sides of the hand/wrist so that
# each motor can counteract tremor from its opposite side.
# -----------------------------------------------------------------------

# ---- MX1508 Channel A - Motor A (one side of the hand) ----
BOARD_IN1 = 6          # GP2  -> MX1508 IN1
BOARD_IN2 = 2          # GP3  -> MX1508 IN2

# ---- MX1508 Channel B - Motor B (opposing side of the hand) ----
BOARD_IN3 = 1          # GP4  -> MX1508 IN3
BOARD_IN4 = 4          # GP5  -> MX1508 IN4

# ---- Onboard status LED ----
LED_PIN = 25           # GP25 -> Pico 2 onboard LED (no resistor needed)


# ===========================================================================
# STEP 2 - BMI160 IMU DRIVER
# ---------------------------------------------------------------------------
# Low-level I2C driver for the BMI160 accelerometer + gyroscope.
# Public API:  imu = BMI160(i2c)
#              ax, ay, az, gx, gy, gz = imu.read_all()
# ===========================================================================

# BMI160 register addresses
_REG_CHIP_ID   = 0x00
_REG_DATA_GYR  = 0x0C  # start of gyro data  (6 bytes: x/y/z, LSB+MSB each)
_REG_DATA_ACC  = 0x12  # start of accel data (6 bytes: x/y/z, LSB+MSB each)
_REG_ACC_CONF  = 0x40
_REG_ACC_RANGE = 0x41
_REG_GYR_CONF  = 0x42
_REG_GYR_RANGE = 0x43
_REG_CMD       = 0x7E

# BMI160 command bytes
_CMD_SOFTRESET  = 0xB6
_CMD_ACC_NORMAL = 0x11  # wake accelerometer from suspend
_CMD_GYR_NORMAL = 0x15  # wake gyroscope from suspend

# ODR / range configuration values
_ACC_CONF_100HZ = 0x28  # 100 Hz output data rate, normal averaging
_GYR_CONF_100HZ = 0x28
_ACC_RANGE_2G   = 0x03  # +/- 2 g
_GYR_RANGE_125  = 0x04  # +/- 125 deg/s

# Physical unit scale factors (raw 16-bit integer -> real unit)
_ACCEL_SCALE = 9.80665 / 16384.0  # m/s^2 per LSB  (for +/- 2 g)
_GYRO_SCALE  = 1.0     / 262.4    # deg/s per LSB  (for +/- 125 deg/s)


class BMI160:
    """Driver for the BMI160 IMU over I2C."""

    def __init__(self, i2c, addr=IMU_ADDR):
        self._i2c  = i2c
        self._addr = addr
        self._init_sensor()

    # ---- low-level register access ----

    def _write(self, reg, val):
        self._i2c.writeto(self._addr, bytes([reg, val]))

    def _read(self, reg, n):
        self._i2c.writeto(self._addr, bytes([reg]))
        buf = bytearray(n)
        self._i2c.readfrom_into(self._addr, buf)
        return buf

    @staticmethod
    def _s16(lo, hi):
        """Two raw bytes -> signed 16-bit integer."""
        v = (hi << 8) | lo
        return v - 65536 if v >= 32768 else v

    # ---- initialisation ----

    def _init_sensor(self):
        """Reset the chip and configure ODR/range for 100 Hz operation."""
        self._write(_REG_CMD, _CMD_SOFTRESET)
        time.sleep_ms(100)
        chip_id = self._read(_REG_CHIP_ID, 1)[0]
        if chip_id != 0xD1:
            raise RuntimeError(
                f"BMI160 not found (chip_id=0x{chip_id:02X}, expected 0xD1). "
                "Check SDA/SCL wiring and I2C address (SDO pin)."
            )
        # Wake sensors up from suspend mode
        self._write(_REG_CMD, _CMD_ACC_NORMAL);  time.sleep_ms(5)
        self._write(_REG_CMD, _CMD_GYR_NORMAL);  time.sleep_ms(80)
        # Set output data rates and measurement ranges
        self._write(_REG_ACC_CONF,  _ACC_CONF_100HZ)
        self._write(_REG_ACC_RANGE, _ACC_RANGE_2G)
        self._write(_REG_GYR_CONF,  _GYR_CONF_100HZ)
        self._write(_REG_GYR_RANGE, _GYR_RANGE_125)
        time.sleep_ms(10)

    def chip_id(self):
        return self._read(_REG_CHIP_ID, 1)[0]

    # ---- data read ----

    def read_all(self):
        """
        Burst-read all 6 axes in one I2C transaction.
        Returns: (ax, ay, az [m/s^2],  gx, gy, gz [deg/s])
        Register 0x0C is the start of gyro data; the next 12 bytes
        contain gyr[0:6] then acc[6:12] consecutively.
        """
        raw = self._read(_REG_DATA_GYR, 12)
        gx = self._s16(raw[0],  raw[1])  * _GYRO_SCALE
        gy = self._s16(raw[2],  raw[3])  * _GYRO_SCALE
        gz = self._s16(raw[4],  raw[5])  * _GYRO_SCALE
        ax = self._s16(raw[6],  raw[7])  * _ACCEL_SCALE
        ay = self._s16(raw[8],  raw[9])  * _ACCEL_SCALE
        az = self._s16(raw[10], raw[11]) * _ACCEL_SCALE
        return ax, ay, az, gx, gy, gz


# ===========================================================================
# STEP 3 - TREMOR DETECTOR
# ---------------------------------------------------------------------------
# Maintains a rolling 1.5-second buffer of accelerometer samples.
# Each call to analyse() returns:
#   - Dominant tremor frequency (Hz)  via zero-crossing count
#   - Dominant tremor axis            (0=X, 1=Y, 2=Z)
#   - Tremor direction sign           (+1 or -1)
#   - Tremor magnitude                (RMS of high-pass filtered signal)
# ===========================================================================

_TREMOR_F_MIN = 2.0   # Hz - ignore frequencies below this (not a tremor)
_TREMOR_F_MAX = 15.0  # Hz - ignore frequencies above this (not a tremor)
_HP_TAU       = 0.1   # s  - high-pass IIR time constant (~1.6 Hz cutoff)
_FREQ_ALPHA   = 0.3   # EMA smoothing weight for frequency estimate


class _HighPassFilter:
    """
    Single-pole high-pass IIR filter.
    Removes gravity and slow-motion components, keeping the tremor signal.
    Formula: y[n] = a * (y[n-1] + x[n] - x[n-1])
    """
    def __init__(self, tau, dt):
        self._a  = tau / (tau + dt)
        self._px = None
        self._py = 0.0

    def reset(self):
        self._px = None
        self._py = 0.0

    def filter(self, x):
        if self._px is None:
            self._px = x
            return 0.0
        y = self._a * (self._py + x - self._px)
        self._px = x
        self._py = y
        return y


class TremorResult:
    """Output of one tremor analysis cycle."""
    __slots__ = ("freq_hz", "magnitude", "axis", "axis_sign")

    def __init__(self, freq_hz, magnitude, axis, axis_sign):
        self.freq_hz   = freq_hz    # estimated tremor frequency in Hz
        self.magnitude = magnitude  # RMS amplitude in m/s^2
        self.axis      = axis       # dominant axis: 0=X, 1=Y, 2=Z
        self.axis_sign = axis_sign  # dominant direction: +1 or -1

    def __repr__(self):
        axis_name = ("X", "Y", "Z")[self.axis]
        sign_char = "+" if self.axis_sign >= 0 else "-"
        return (f"f_tremor={self.freq_hz:.2f}Hz  "
                f"magnitude={self.magnitude:.4f}m/s^2  "
                f"axis={sign_char}{axis_name}")


class TremorDetector:
    """
    Accumulates IMU samples into a rolling circular buffer and estimates
    the tremor properties on demand.

    Usage:
        td = TremorDetector(sample_rate_hz=100, window_sec=1.5)
        td.update(ax, ay, az)          # call every sample
        if td.ready():
            result = td.analyse()      # returns TremorResult or None
    """

    def __init__(self, sample_rate_hz=100, window_sec=1.5):
        self._fs   = sample_rate_hz
        self._dt   = 1.0 / sample_rate_hz
        self._n    = int(sample_rate_hz * window_sec)  # buffer length in samples
        self._win  = window_sec

        # Circular buffers for raw and high-pass filtered data (one per axis)
        self._raw  = [[0.0] * self._n for _ in range(3)]
        self._filt = [[0.0] * self._n for _ in range(3)]
        self._hp   = [_HighPassFilter(_HP_TAU, self._dt) for _ in range(3)]

        self._idx         = 0      # next write position in circular buffer
        self._count       = 0      # total samples received so far
        self._smooth_freq = 0.0    # EMA-smoothed frequency estimate

    def update(self, ax, ay, az):
        """Add one new accelerometer sample. Call at sample_rate_hz."""
        raw = (ax, ay, az)
        for i in range(3):
            self._raw[i][self._idx]  = raw[i]
            self._filt[i][self._idx] = self._hp[i].filter(raw[i])
        self._idx = (self._idx + 1) % self._n
        if self._count < self._n:
            self._count += 1

    def ready(self):
        """True once the buffer contains at least one full window."""
        return self._count >= self._n

    def analyse(self):
        """
        Analyse the current buffer window and return a TremorResult.
        Returns None if the buffer is not yet full.

        Algorithm:
          1. Compute RMS of the high-pass filtered signal on each axis.
          2. Axis with highest RMS is the dominant (tremor) axis.
          3. Sign of the raw signal mean gives the tremor direction.
          4. Count zero-crossings on the filtered dominant axis.
             tremor_frequency = (zero_crossings / 2) / window_seconds
          5. Smooth the frequency estimate with an EMA filter.
        """
        if not self.ready():
            return None

        # Step 1 + 2: dominant axis by RMS amplitude
        rms = [
            math.sqrt(sum(v * v for v in self._filt[i]) / self._n)
            for i in range(3)
        ]
        dom = rms.index(max(rms))

        # Step 3: tremor direction from raw signal mean on dominant axis
        raw_mean  = sum(self._raw[dom]) / self._n
        axis_sign = 1 if raw_mean >= 0 else -1

        # Step 4: zero-crossing frequency estimate
        ordered   = [self._filt[dom][(self._idx + i) % self._n]
                     for i in range(self._n)]
        crossings = sum(1 for j in range(1, self._n)
                        if ordered[j - 1] * ordered[j] < 0)
        raw_freq  = (crossings / 2.0) / self._win

        # Step 5: update smoothed frequency only when within plausible range
        if _TREMOR_F_MIN <= raw_freq <= _TREMOR_F_MAX:
            self._smooth_freq = (
                _FREQ_ALPHA * raw_freq
                + (1.0 - _FREQ_ALPHA) * self._smooth_freq
            )

        return TremorResult(
            freq_hz   = self._smooth_freq,
            magnitude = rms[dom],
            axis      = dom,
            axis_sign = axis_sign,
        )


# ===========================================================================
# STEP 4 - MOTOR CONTROLLER  (1x MX1508 dual H-bridge board, 2x N20 motors)
# ---------------------------------------------------------------------------
# The single MX1508 board drives both motors via its four input pins:
#   Channel A:  IN1 + IN2  ->  Motor A
#   Channel B:  IN3 + IN4  ->  Motor B
#
# Per-channel drive logic:
#   Drive forward:  IN_A = duty,  IN_B = 0
#   Brake:          IN_A = max,   IN_B = max
#   Coast (idle):   IN_A = 0,     IN_B = 0
#
# Vibration is produced by pulsing each motor ON/OFF at f_motor Hz using a
# phase accumulator that runs in step with the 100 Hz control loop.
# ===========================================================================

_MOTOR_CARRIER_HZ = 1000  # PWM carrier frequency (smooth motor drive)

# Motor ID constants - used throughout the code
MOTOR_A = 0   # MX1508 Channel A  (IN1/IN2) - one side of the hand
MOTOR_B = 1   # MX1508 Channel B  (IN3/IN4) - opposing side of the hand
MOTOR_NAMES = ["MOTOR_A", "MOTOR_B"]

# Pin pairs (IN_pos, IN_neg) for each motor channel
_MOTOR_PINS = [
    (BOARD_IN1, BOARD_IN2),   # Motor A - MX1508 Channel A
    (BOARD_IN3, BOARD_IN4),   # Motor B - MX1508 Channel B
]


class MotorController:
    """
    Controls both N20 motors via the single MX1508 H-bridge board.
    Vibration is created by pulsing motor ON/OFF at the desired frequency.
    Call update_vibration() once per IMU sample to advance the phase.
    """

    def __init__(self, pin_pairs, carrier_hz=_MOTOR_CARRIER_HZ):
        self._pwm = []
        for in1, in2 in pin_pairs:
            p1 = PWM(Pin(in1));  p1.freq(carrier_hz)
            p2 = PWM(Pin(in2));  p2.freq(carrier_hz)
            self._pwm.append((p1, p2))
        self._phase    = [0.0] * len(pin_pairs)
        self._n_motors = len(pin_pairs)

    def coast(self, motor_id):
        """Unpowered - motor spins down freely."""
        p1, p2 = self._pwm[motor_id]
        p1.duty_u16(0);  p2.duty_u16(0)

    def brake(self, motor_id):
        """Active brake - motor stops quickly."""
        p1, p2 = self._pwm[motor_id]
        p1.duty_u16(65535);  p2.duty_u16(65535)

    def drive(self, motor_id, duty_0to1):
        """Drive motor forward at duty_0to1 (0.0 = off, 1.0 = full speed)."""
        duty = int(max(0.0, min(1.0, duty_0to1)) * 65535)
        p1, p2 = self._pwm[motor_id]
        p1.duty_u16(duty);  p2.duty_u16(0)

    def stop_all(self):
        """Coast all motors - safe idle state."""
        for i in range(self._n_motors):
            self.coast(i)

    def update_vibration(self, motor_id, f_motor_hz, intensity, sample_rate_hz):
        """
        Advance vibration phase for one motor. Call once per sample.
        Motor is ON for the first half of each period, OFF for the second half.

        Args:
            motor_id       : which motor (0-3)
            f_motor_hz     : vibration frequency in Hz
            intensity      : drive strength during ON phase  (0.0 - 1.0)
            sample_rate_hz : how often this is called (must match main loop)
        """
        if f_motor_hz <= 0:
            self.coast(motor_id)
            return

        period = sample_rate_hz / f_motor_hz   # period in sample counts

        self._phase[motor_id] += 1.0
        if self._phase[motor_id] >= period:
            self._phase[motor_id] = 0.0

        # First half-period: motor ON (vibration pulse)
        # Second half-period: motor OFF (rest)
        if self._phase[motor_id] < (period / 2.0):
            self.drive(motor_id, intensity)
        else:
            self.coast(motor_id)


# ===========================================================================
# STEP 5 - 433 MHz TRANSMITTER  (FS1000A, glove -> base telemetry)
# ---------------------------------------------------------------------------
# Custom UART-over-OOK framing at 500 bit/s (reliable for 433 MHz modules).
# Frame structure:
#   [0xAA x 12 preamble bytes]  [0x55 start byte]  [length byte]
#   [payload bytes]             [checksum byte]
#
# Telemetry payload (11 bytes, big-endian):
#   f_tremor   uint16  Hz x 100
#   magnitude  uint16  m/s^2 x 100
#   axis_byte  uint8   high nibble=axis(0/1/2), low bit=sign(0=+, 1=-)
#   motor_id   uint8   0-3
#   f_motor    uint16  Hz x 100
#   k_factor   uint8   k x 10
#   mode       uint8   0=normal, 1=calibration, 2=continuous_on, 3=off
# ===========================================================================

_TX_BIT_US   = 2000   # microseconds per bit -> 500 bit/s
_TX_PREAMBLE = 12     # number of 0xAA sync bytes per packet
_TELEM_FMT   = ">HHBBHBB"


def _tx_bit(pin, b):
    pin.value(b)
    utime.sleep_us(_TX_BIT_US)


def _tx_byte(pin, val):
    _tx_bit(pin, 0)                        # start bit (LOW)
    for i in range(8):
        _tx_bit(pin, (val >> i) & 1)       # 8 data bits, LSB first
    _tx_bit(pin, 1)                        # stop bit (HIGH)


def rf_send_packet(tx_pin, payload: bytes):
    """
    Transmit a framed RF packet.
    tx_pin   : machine.Pin object (output mode)
    payload  : raw bytes to send as packet payload
    """
    for _ in range(_TX_PREAMBLE):
        _tx_byte(tx_pin, 0xAA)             # sync preamble
    _tx_byte(tx_pin, 0x55)                 # packet start marker
    _tx_byte(tx_pin, len(payload))         # payload length

    csum = 0
    for b in payload:
        _tx_byte(tx_pin, b)
        csum = (csum + b) & 0xFF           # accumulate checksum
    _tx_byte(tx_pin, csum)                 # trailing checksum byte


def build_telemetry_packet(f_tremor, magnitude, axis, axis_sign,
                           motor_id, f_motor, k_factor, mode):
    """
    Encode tremor/motor data into the 11-byte telemetry payload.
    Floats are scaled to integers to fit compact packet fields.
    """
    ft   = int(f_tremor  * 100) & 0xFFFF
    mag  = int(magnitude * 100) & 0xFFFF
    axb  = ((axis & 0x0F) << 4) | (0 if axis_sign >= 0 else 1)
    fm   = int(f_motor   * 100) & 0xFFFF
    k    = int(k_factor  * 10)  & 0xFF
    m    = int(mode)             & 0xFF
    return struct.pack(_TELEM_FMT, ft, mag, axb, motor_id, fm, k, m)


# ===========================================================================
# STEP 6 - 433 MHz RECEIVER  (XY-MK-5V, base -> glove config packets)
# ---------------------------------------------------------------------------
# Interrupt-driven bit decoder. Pin IRQ fires on every rising/falling edge;
# we measure the time between edges to reconstruct bits, then bytes, then
# validate the packet frame and push complete payloads to _cfg_packets.
#
# Config payload (3 bytes, big-endian):
#   mode            uint8   0=normal, 1=calibration, 2=continuous_on, 3=off
#   k_factor        uint8   k x 10   (e.g. 30 means k=3.0)
#   intensity_limit uint8   limit x 100  (e.g. 80 means 0.80)
# ===========================================================================

_RX_BIT_US  = 2000
_HALF_BIT   = _RX_BIT_US // 2
_CFG_FMT    = ">BBB"
_CFG_LEN    = struct.calcsize(_CFG_FMT)   # 3 bytes

# Receiver state - written in IRQ context, read in main loop
_cfg_last_us   = 0
_cfg_bits      = []
_cfg_buf       = []
_cfg_packets   = []    # validated config payloads accumulate here

_CFG_ST_PREAMBLE = 0
_CFG_ST_LEN      = 1
_CFG_ST_DATA     = 2
_CFG_ST_CSUM     = 3

_cfg_state    = _CFG_ST_PREAMBLE
_cfg_rx_len   = 0
_cfg_rx_csum  = 0


def _cfg_push_bit(bit):
    """Accumulate bits. On every 10th (start+8data+stop), decode a byte."""
    global _cfg_bits
    _cfg_bits.append(bit)
    if len(_cfg_bits) == 10:
        start = _cfg_bits[0]
        stop  = _cfg_bits[9]
        val   = 0
        for i in range(8):
            val |= (_cfg_bits[1 + i] << i)
        _cfg_bits = []
        if start == 0 and stop == 1:   # valid UART framing
            _cfg_push_byte(val)


def _cfg_push_byte(b):
    """State machine: assemble bytes into a validated config packet."""
    global _cfg_state, _cfg_rx_len, _cfg_rx_csum, _cfg_buf, _cfg_bits

    if _cfg_state == _CFG_ST_PREAMBLE:
        if b == 0x55:                       # start marker found
            _cfg_state = _CFG_ST_LEN

    elif _cfg_state == _CFG_ST_LEN:
        _cfg_rx_len  = b
        _cfg_rx_csum = 0
        _cfg_buf     = []
        _cfg_state   = _CFG_ST_DATA

    elif _cfg_state == _CFG_ST_DATA:
        _cfg_buf.append(b)
        _cfg_rx_csum = (_cfg_rx_csum + b) & 0xFF
        if len(_cfg_buf) >= _cfg_rx_len:
            _cfg_state = _CFG_ST_CSUM

    elif _cfg_state == _CFG_ST_CSUM:
        if b == _cfg_rx_csum and len(_cfg_buf) == _CFG_LEN:
            _cfg_packets.append(bytes(_cfg_buf))   # valid packet!
        _cfg_state = _CFG_ST_PREAMBLE
        _cfg_bits  = []


def _cfg_rx_irq(pin):
    """Pin IRQ handler - fires on every edge of the RX signal."""
    global _cfg_last_us
    now = utime.ticks_us()
    dt  = utime.ticks_diff(now, _cfg_last_us)
    _cfg_last_us = now

    n = (dt + _HALF_BIT) // _RX_BIT_US   # number of bit periods elapsed
    if n < 1 or n > 20:
        return                             # out of range - ignore noise

    level = pin.value()
    for _ in range(n):
        _cfg_push_bit(level)


def rx_get_config():
    """
    Non-blocking check for a received config packet.
    Returns a dict with keys {mode, k_factor, intensity_limit} or None.
    """
    if not _cfg_packets:
        return None
    raw = _cfg_packets.pop(0)
    try:
        mode_raw, k_raw, lim_raw = struct.unpack(_CFG_FMT, raw)
        return {
            "mode"            : mode_raw,
            "k_factor"        : k_raw  / 10.0,
            "intensity_limit" : lim_raw / 100.0,
        }
    except Exception:
        return None


# ===========================================================================
# STEP 7 - SYSTEM CONFIGURATION STATE
# ---------------------------------------------------------------------------
# Stores the current operating parameters. Initialised to safe defaults;
# updated whenever a valid config packet arrives from the base Pico.
# ===========================================================================

class SystemConfig:
    """
    Central config for the glove Pico.
    All values are read by the control loop on every iteration.
    """
    MODE_NORMAL      = 0
    MODE_CALIBRATION = 1
    MODE_CONTINUOUS  = 2
    MODE_OFF         = 3

    def __init__(self):
        self.mode            = self.MODE_NORMAL
        self.k_factor        = 3.0   # f_motor = k_factor * f_tremor
        self.intensity_limit = 1.0   # global intensity cap (0.0 - 1.0)

    def apply(self, cfg_dict):
        """Apply a decoded config dict, clamping values to safe ranges."""
        if cfg_dict is None:
            return
        self.mode            = int(cfg_dict.get("mode",            self.mode))
        self.k_factor        = float(cfg_dict.get("k_factor",        self.k_factor))
        self.intensity_limit = float(cfg_dict.get("intensity_limit", self.intensity_limit))
        # Safety clamps
        self.k_factor        = max(0.1,  min(25.0, self.k_factor))
        self.intensity_limit = max(0.0,  min(1.0,  self.intensity_limit))
        self.mode            = max(0,    min(3,    self.mode))


# ===========================================================================
# STEP 8 - TREMOR-TO-MOTOR MAPPING
# ---------------------------------------------------------------------------
# Maps detected tremor axis + direction to the OPPOSING motor.
# "Opposing" = the motor mounted on the side directly opposite the tremor,
# so its vibration counteracts the tremor direction.
#
# Anatomical reference (hand palm-down, fingers forward):
#   +X = thumb / radial side     -X = pinky / ulnar side
#   +Y = dorsal (back of hand)   -Y = volar (palm side)
#   +Z = upward when palm-down   -Z = downward
#
# Adjust this table if your IMU is mounted in a different orientation.
# ===========================================================================

_AXIS_X = 0
_AXIS_Y = 1
_AXIS_Z = 2

# (axis, sign) -> motor_id to activate (the motor opposing the tremor)
# With only 2 motors the rule is simple:
#   positive tremor direction -> Motor B opposes
#   negative tremor direction -> Motor A opposes
# When you physically mount the motors, orient them so A and B face each other.
TREMOR_TO_MOTOR_MAP = {
    (_AXIS_X, +1): MOTOR_B,   # +X tremor -> oppose with Motor B
    (_AXIS_X, -1): MOTOR_A,   # -X tremor -> oppose with Motor A
    (_AXIS_Y, +1): MOTOR_B,   # +Y tremor -> oppose with Motor B
    (_AXIS_Y, -1): MOTOR_A,   # -Y tremor -> oppose with Motor A
    (_AXIS_Z, +1): MOTOR_B,   # +Z tremor -> oppose with Motor B
    (_AXIS_Z, -1): MOTOR_A,   # -Z tremor -> oppose with Motor A
}

# RMS magnitude that maps to 100% motor intensity.
# Tune this during calibration - typical resting tremor: 0.5-3 m/s^2
MAGNITUDE_SCALE = 2.0   # m/s^2


def select_motor(tremor_result):
    """Return the motor ID that should oppose the detected tremor."""
    key = (tremor_result.axis, tremor_result.axis_sign)
    return TREMOR_TO_MOTOR_MAP.get(key, MOTOR_A)


def calc_intensity(tremor_result, intensity_limit):
    """
    Map tremor magnitude to motor drive intensity (0.0 - 1.0).
    Scales linearly up to MAGNITUDE_SCALE, then clamps to intensity_limit.
    """
    raw = tremor_result.magnitude / MAGNITUDE_SCALE
    return min(raw, intensity_limit)


# ===========================================================================
# STEP 9 - MAIN CLOSED-LOOP CONTROL
# ---------------------------------------------------------------------------
# Initialises all hardware, then runs a 100 Hz control loop that:
#   A. Reads IMU
#   B. Updates tremor buffer
#   C. Analyses tremor (once buffer is full)
#   D. Drives the opposing motor at f_motor = k * f_tremor
#   E. Checks for incoming config updates via RF
#   F. Transmits telemetry to base Pico at 10 Hz
#   G. Prints a status line at 1 Hz
# ===========================================================================

SAMPLE_RATE_HZ   = 100
SAMPLE_PERIOD_MS = 1000 // SAMPLE_RATE_HZ   # 10 ms per sample

TELEM_RATE_HZ = 10
TELEM_EVERY   = SAMPLE_RATE_HZ // TELEM_RATE_HZ   # transmit every N samples

# ---- Initialise hardware ----

print("=" * 50)
print("  SteadiARM Glove Pico - Startup")
print("=" * 50)

# Status LED
led = Pin(LED_PIN, Pin.OUT)
led.value(1)

# IMU
i2c = I2C(IMU_I2C_BUS, sda=Pin(IMU_SDA_PIN), scl=Pin(IMU_SCL_PIN), freq=IMU_FREQ)
try:
    imu = BMI160(i2c)
    print(f"[OK] BMI160 chip_id=0x{imu.chip_id():02X}")
except RuntimeError as e:
    print(f"[ERR] IMU: {e}")
    led.value(0)
    raise

# Motors
motors = MotorController(_MOTOR_PINS)
motors.stop_all()
print("[OK] Motors initialised (all stopped)")

# Tremor detector
tremor_detector = TremorDetector(sample_rate_hz=SAMPLE_RATE_HZ, window_sec=1.5)
print(f"[OK] Tremor detector ready (window={SAMPLE_RATE_HZ * 1.5:.0f} samples)")

# RF Transmitter
tx_pin = Pin(TX_PIN, Pin.OUT, value=0)
print(f"[OK] RF TX ready on GP{TX_PIN}")

# RF Receiver (interrupt-driven)
rx_pin = Pin(RX_PIN, Pin.IN)
rx_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=_cfg_rx_irq)
print(f"[OK] RF RX listening on GP{RX_PIN}")

# System config (defaults until first RF config packet arrives)
config = SystemConfig()
print(f"[OK] Config defaults: mode=NORMAL  k={config.k_factor}  limit={config.intensity_limit}")

# ---- Main control loop ----

print()
print("Entering closed-loop at 100 Hz. Ctrl-C to stop.")
print()

sample_count  = 0
active_motor  = MOTOR_A        # current active motor
f_motor_hz    = 0.0            # current motor vibration frequency
intensity     = 0.0            # current motor intensity
last_result   = None           # most recent TremorResult (cached)
latched_valid = False          # profile-2: holds counter-frequency until OFF
t_next        = time.ticks_ms()

try:
    while True:
        # ---- Wait for next 10 ms sample tick ----
        now  = time.ticks_ms()
        wait = time.ticks_diff(t_next, now)
        if wait > 0:
            time.sleep_ms(wait)
        t_next = time.ticks_add(t_next, SAMPLE_PERIOD_MS)

        # ---- STAGE A: Read IMU ----
        ax, ay, az, gx, gy, gz = imu.read_all()

        # ---- STAGE B: Feed sample into tremor detector buffer ----
        tremor_detector.update(ax, ay, az)
        sample_count += 1

        # ---- STAGE C: Analyse tremor (only once buffer is full) ----
        if tremor_detector.ready():
            last_result = tremor_detector.analyse()

            if last_result and last_result.freq_hz > 0:
                # Valid tremor detected - compute motor target
                detected_motor     = select_motor(last_result)
                detected_f_motor   = config.k_factor * last_result.freq_hz
                detected_intensity = calc_intensity(last_result, config.intensity_limit)

                if config.mode in (SystemConfig.MODE_NORMAL, SystemConfig.MODE_CALIBRATION):
                    active_motor = detected_motor
                    f_motor_hz   = detected_f_motor
                    intensity    = detected_intensity
                    latched_valid = False
                elif config.mode == SystemConfig.MODE_CONTINUOUS:
                    # Latch and keep vibrating until user sends OFF (mode=3).
                    active_motor  = detected_motor
                    f_motor_hz    = detected_f_motor
                    intensity     = detected_intensity
                    latched_valid = True
            else:
                if config.mode in (SystemConfig.MODE_NORMAL, SystemConfig.MODE_CALIBRATION):
                    # In normal/calibration mode: no tremor -> stop motors.
                    motors.stop_all()
                    f_motor_hz = 0.0
                    intensity  = 0.0
                    latched_valid = False
                elif config.mode == SystemConfig.MODE_OFF:
                    # Forced OFF mode always clears any previous latch.
                    motors.stop_all()
                    f_motor_hz = 0.0
                    intensity  = 0.0
                    latched_valid = False
                # In continuous mode with no fresh tremor, keep last latched output.

        # ---- STAGE D: Update motor vibration ----
        # Only the selected (opposing) motor runs; all others coast.
        if config.mode == SystemConfig.MODE_OFF:
            motors.stop_all()
            f_motor_hz = 0.0
            intensity = 0.0
            latched_valid = False
        for mid in range(2):
            if mid == active_motor and f_motor_hz > 0 and (config.mode != SystemConfig.MODE_CONTINUOUS or latched_valid):
                motors.update_vibration(mid, f_motor_hz, intensity, SAMPLE_RATE_HZ)
            else:
                motors.coast(mid)

        # ---- STAGE E: Check for config update from base Pico via RF RX ----
        cfg = rx_get_config()
        if cfg is not None:
            config.apply(cfg)
            print(f"[CFG] mode={cfg['mode']}  "
                  f"k={cfg['k_factor']:.1f}  "
                  f"limit={cfg['intensity_limit']:.2f}")
            if config.mode == SystemConfig.MODE_OFF:
                motors.stop_all()
                f_motor_hz = 0.0
                intensity = 0.0
                latched_valid = False

        # ---- STAGE F: Transmit telemetry to base Pico at 10 Hz ----
        if sample_count % TELEM_EVERY == 0 and last_result is not None:
            pkt = build_telemetry_packet(
                f_tremor  = last_result.freq_hz,
                magnitude = last_result.magnitude,
                axis      = last_result.axis,
                axis_sign = last_result.axis_sign,
                motor_id  = active_motor,
                f_motor   = f_motor_hz,
                k_factor  = config.k_factor,
                mode      = config.mode,
            )
            rf_send_packet(tx_pin, pkt)

        # ---- STAGE G: Status print at ~1 Hz (every 100 samples) ----
        if sample_count % 100 == 0:
            if last_result:
                mode_str = {
                    SystemConfig.MODE_NORMAL: "NORM",
                    SystemConfig.MODE_CALIBRATION: "CAL",
                    SystemConfig.MODE_CONTINUOUS: "CONT",
                    SystemConfig.MODE_OFF: "OFF",
                }.get(config.mode, str(config.mode))
                print(f"[{sample_count:6d}] {last_result}"
                      f"  -> motor={MOTOR_NAMES[active_motor]}"
                      f"  f_m={f_motor_hz:.2f}Hz"
                      f"  intensity={intensity:.2f}"
                      f"  mode={mode_str}  k={config.k_factor:.1f}")
            led.toggle()   # blink onboard LED to confirm loop is running

except KeyboardInterrupt:
    motors.stop_all()
    led.value(0)
    print("\n[STOP] Glove Pico stopped cleanly.")
