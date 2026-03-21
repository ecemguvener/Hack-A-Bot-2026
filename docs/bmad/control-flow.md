# Control-Flow Sketch
> Keep mode logic simple (`NORMAL`, `CALIBRATION`, `SAFE`) so debugging is faster.

## Node A (Glove, closed loop)

```text
INIT
  -> IMU init
  -> RF init
  -> motor driver init
  -> load default config (mode, k, limits)

MAIN LOOP (100 Hz)
  1) Read IMU sample
  2) Validate sample
     - invalid -> set fault, stop/limit motor, continue
  3) Push sample to rolling window (1-2 s)
  4) Compute per-axis RMS/variance
  5) Select dominant axis + sign
  6) Filter dominant-axis signal (HP/BP)
  7) Estimate f_tremor using zero-crossings in window
     f_tremor = (zero_crossings / 2) / window_seconds
  8) Smooth f_tremor and magnitude
  9) Determine opposing motor from axis/sign map
 10) Compute f_motor = clamp(k_factor * f_tremor, f_min, f_max)
 11) Compute duty from magnitude and intensity_limit
 12) Drive selected motor
 13) Check RF timeout
      - timeout -> safe fallback output
 14) Send telemetry to Node B at 10-20 Hz
 15) Apply any new config packet (mode, k, limits)
```

## Node B (Base bridge)

```text
INIT
  -> RF init
  -> PC link init (WebSocket/HTTP/TCP)

MAIN LOOP
  1) RX telemetry from Node A
  2) Store/update latest state
  3) Forward telemetry to PC UI
  4) Read PC UI config changes
  5) TX config to Node A
```

## Modes
- `NORMAL`: full closed-loop control
- `CALIBRATION`: user adjusts `k_factor`; telemetry continues for comparison
- `SAFE`: entered on RF/IMU fault with bounded or disabled motor output
