# Control-Flow Sketch

## Node A (Device Loop)

```text
INIT
  -> sensor init
  -> RF init
  -> calibration window
  -> mode = IDLE

MAIN LOOP (100 Hz)
  1) Read IMU
  2) Validate sample
     - if invalid -> fault flag + safe output
  3) Estimate orientation/features
  4) Compute metrics
     - tremor amplitude proxy
     - smoothness score
     - stability score
  5) If assist enabled:
     - evaluate candidate profile response
     - choose/update active profile
     - compute output command (bounded)
     - apply command
     else:
     - output neutral/minimum
  6) Check RF heartbeat timeout
     - timeout -> safe output + link_lost flag
  7) Periodic telemetry TX to Node B
```

## Node B (Companion Loop)

```text
INIT
  -> input init (joystick/buttons)
  -> OLED init
  -> RF init

MAIN LOOP (~20-50 Hz)
  1) Read user inputs
  2) Build control packet
     - mode
     - profile
     - assist enable
     - heartbeat
  3) TX packet to Node A
  4) RX telemetry from Node A
  5) Update OLED
     - mode/profile
     - metrics
     - link/fault status
```

## State Machine (A)
- `IDLE`: no assist output
- `BASELINE`: metric capture without assist
- `ASSIST`: adaptive support active
- `SAFE`: fallback after RF/sensor fault
