"""
SteadiARM – Glove Pi (Pico 2)
BMI160 IMU integration + tremor detection

Wiring:
    BMI160 SDA → GP0  (pin 1)
    BMI160 SCL → GP1  (pin 2)
    BMI160 VCC → 3.3V
    BMI160 GND → GND
    BMI160 SDO → GND  (I2C address 0x68)
"""

from machine import I2C, Pin
import time
import math

# ══════════════════════════════════════════════════════════════════════════════
# BMI160 DRIVER
# ══════════════════════════════════════════════════════════════════════════════

_REG_CHIP_ID    = 0x00
_REG_DATA_GYR   = 0x0C   # 6 bytes: gyr x/y/z LSB+MSB
_REG_DATA_ACC   = 0x12   # 6 bytes: acc x/y/z LSB+MSB
_REG_ACC_CONF   = 0x40
_REG_ACC_RANGE  = 0x41
_REG_GYR_CONF   = 0x42
_REG_GYR_RANGE  = 0x43
_REG_CMD        = 0x7E

_CMD_ACC_NORMAL = 0x11
_CMD_GYR_NORMAL = 0x15
_CMD_SOFTRESET  = 0xB6

_ACC_CONF_100HZ = 0x28   # ODR = 100 Hz, normal avg
_GYR_CONF_100HZ = 0x28
_ACC_RANGE_2G   = 0x03   # ±2 g
_GYR_RANGE_125  = 0x04   # ±125 °/s

_ACCEL_SCALE    = 9.80665 / 16384.0   # m/s² per LSB
_GYRO_SCALE     = 1.0 / 262.4         # °/s  per LSB

_I2C_ADDR       = 0x68


class BMI160:
    def __init__(self, i2c, addr=_I2C_ADDR):
        self._i2c  = i2c
        self._addr = addr
        self._init()

    def _write(self, reg, val):
        self._i2c.writeto(self._addr, bytes([reg, val]))

    def _read(self, reg, n):
        self._i2c.writeto(self._addr, bytes([reg]))
        buf = bytearray(n)
        self._i2c.readfrom_into(self._addr, buf)
        return buf

    @staticmethod
    def _s16(lo, hi):
        v = (hi << 8) | lo
        return v - 65536 if v >= 32768 else v

    def _init(self):
        self._write(_REG_CMD, _CMD_SOFTRESET)
        time.sleep_ms(100)
        cid = self._read(_REG_CHIP_ID, 1)[0]
        if cid != 0xD1:
            raise RuntimeError(f"BMI160 not found (chip_id=0x{cid:02X}, expected 0xD1)")
        self._write(_REG_CMD, _CMD_ACC_NORMAL);  time.sleep_ms(5)
        self._write(_REG_CMD, _CMD_GYR_NORMAL);  time.sleep_ms(80)
        self._write(_REG_ACC_CONF,  _ACC_CONF_100HZ)
        self._write(_REG_ACC_RANGE, _ACC_RANGE_2G)
        self._write(_REG_GYR_CONF,  _GYR_CONF_100HZ)
        self._write(_REG_GYR_RANGE, _GYR_RANGE_125)
        time.sleep_ms(10)

    def chip_id(self):
        return self._read(_REG_CHIP_ID, 1)[0]

    def read_all(self):
        """Returns (ax, ay, az m/s², gx, gy, gz °/s) in one burst read."""
        raw = self._read(_REG_DATA_GYR, 12)   # gyr[0:6] + acc[6:12]
        gx = self._s16(raw[0],  raw[1])  * _GYRO_SCALE
        gy = self._s16(raw[2],  raw[3])  * _GYRO_SCALE
        gz = self._s16(raw[4],  raw[5])  * _GYRO_SCALE
        ax = self._s16(raw[6],  raw[7])  * _ACCEL_SCALE
        ay = self._s16(raw[8],  raw[9])  * _ACCEL_SCALE
        az = self._s16(raw[10], raw[11]) * _ACCEL_SCALE
        return ax, ay, az, gx, gy, gz


# ══════════════════════════════════════════════════════════════════════════════
# TREMOR DETECTION
# ══════════════════════════════════════════════════════════════════════════════

_TREMOR_FMIN = 2.0    # Hz – lowest plausible tremor frequency
_TREMOR_FMAX = 15.0   # Hz – highest plausible tremor frequency
_HP_TAU      = 0.1    # s  – high-pass time constant (~1.6 Hz cutoff)
_FREQ_ALPHA  = 0.3    # EMA weight for frequency smoothing


class _HighPass:
    """Single-pole high-pass IIR: y[n] = alpha*(y[n-1] + x[n] - x[n-1])"""
    def __init__(self, tau, dt):
        self._a = tau / (tau + dt)
        self._px = None
        self._py = 0.0

    def reset(self):
        self._px = None;  self._py = 0.0

    def filter(self, x):
        if self._px is None:
            self._px = x;  return 0.0
        y = self._a * (self._py + x - self._px)
        self._px = x;  self._py = y
        return y


class TremorResult:
    __slots__ = ("freq_hz", "magnitude", "axis", "axis_sign")
    def __init__(self, freq_hz, magnitude, axis, axis_sign):
        self.freq_hz   = freq_hz    # Hz
        self.magnitude = magnitude  # m/s² RMS
        self.axis      = axis       # 0=x, 1=y, 2=z
        self.axis_sign = axis_sign  # +1 or -1

    def __repr__(self):
        name = ("X", "Y", "Z")[self.axis]
        sign = "+" if self.axis_sign >= 0 else "-"
        return (f"f={self.freq_hz:.2f} Hz  "
                f"mag={self.magnitude:.4f} m/s²  "
                f"axis={sign}{name}")


class TremorDetector:
    def __init__(self, sample_rate_hz=100, window_sec=1.5):
        self._fs  = sample_rate_hz
        self._dt  = 1.0 / sample_rate_hz
        self._n   = int(sample_rate_hz * window_sec)
        self._win = window_sec

        self._buf  = [[0.0] * self._n for _ in range(3)]
        self._filt = [[0.0] * self._n for _ in range(3)]
        self._hp   = [_HighPass(_HP_TAU, self._dt) for _ in range(3)]
        self._idx  = 0
        self._cnt  = 0
        self._smooth_freq = 0.0

    def update(self, ax, ay, az):
        raw = (ax, ay, az)
        for i in range(3):
            self._buf[i][self._idx]  = raw[i]
            self._filt[i][self._idx] = self._hp[i].filter(raw[i])
        self._idx = (self._idx + 1) % self._n
        if self._cnt < self._n:
            self._cnt += 1

    def ready(self):
        return self._cnt >= self._n

    def analyse(self):
        if not self.ready():
            return None

        # RMS per axis on filtered signal → dominant axis
        rms = [math.sqrt(sum(v*v for v in self._filt[i]) / self._n) for i in range(3)]
        dom = rms.index(max(rms))

        # Mean of raw signal gives dominant direction sign
        raw_mean  = sum(self._buf[dom]) / self._n
        axis_sign = 1 if raw_mean >= 0 else -1

        # Zero-crossing frequency on filtered dominant axis
        samples   = self._ordered(self._filt[dom])
        crossings = sum(1 for j in range(1, self._n) if samples[j-1]*samples[j] < 0)
        freq      = (crossings / 2.0) / self._win

        if _TREMOR_FMIN <= freq <= _TREMOR_FMAX:
            self._smooth_freq = _FREQ_ALPHA * freq + (1 - _FREQ_ALPHA) * self._smooth_freq

        return TremorResult(self._smooth_freq, rms[dom], dom, axis_sign)

    def _ordered(self, buf):
        """Return circular buffer as a list, oldest → newest."""
        return [buf[(self._idx + i) % self._n] for i in range(self._n)]


# ══════════════════════════════════════════════════════════════════════════════
# MAIN – sample loop
# ══════════════════════════════════════════════════════════════════════════════

SAMPLE_RATE_HZ  = 100
SAMPLE_PERIOD_MS = 1000 // SAMPLE_RATE_HZ   # 10 ms

i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400_000)
imu = BMI160(i2c)
print(f"BMI160 chip_id = 0x{imu.chip_id():02X}  (expect 0xD1)")

td = TremorDetector(sample_rate_hz=SAMPLE_RATE_HZ, window_sec=1.5)

print("\nSampling at 100 Hz — Ctrl-C to stop\n")
print(f"{'ax':>8} {'ay':>8} {'az':>8}  {'gx':>8} {'gy':>8} {'gz':>8}   tremor analysis")
print("-" * 90)

sample_count = 0
t_next = time.ticks_ms()

try:
    while True:
        now  = time.ticks_ms()
        wait = time.ticks_diff(t_next, now)
        if wait > 0:
            time.sleep_ms(wait)
        t_next = time.ticks_add(t_next, SAMPLE_PERIOD_MS)

        ax, ay, az, gx, gy, gz = imu.read_all()
        td.update(ax, ay, az)
        sample_count += 1

        # Print at ~10 Hz
        if sample_count % 10 == 0:
            info = ""
            if td.ready():
                r = td.analyse()
                if r:
                    info = f"   {r}"
            print(f"{ax:8.4f} {ay:8.4f} {az:8.4f}  {gx:8.3f} {gy:8.3f} {gz:8.3f}{info}")

except KeyboardInterrupt:
    print("\nStopped.")
