# Block Diagram
> Keep this on one page. While talking, literally point at boxes so judges can follow fast.

```text
+--------------------------------------------------------------------------+
| Node B: Base Pico (Bridge + Config + UI Forwarder)                      |
|--------------------------------------------------------------------------|
| 433 RX (XY-MK-5V, level-shifted) receives glove telemetry               |
| 433 TX (FS1000A) sends config: mode, k_factor, intensity_limit          |
| USB serial to laptop                                                     |
| JSON bridge to WebSocket dashboard (serial_ws_bridge.py)                |
| User controls: calibration / normal / continuous_on / off               |
+-----------------------------------+--------------------------------------+
                                    |
                                    | 433 MHz telemetry + config packets
                                    v
+--------------------------------------------------------------------------+
| Node A: VibraARM Glove Pico                                              |
|--------------------------------------------------------------------------|
| BMI160 @ 100 Hz -> rolling window (1.5 s)                                |
| -> high-pass filter + dominant axis/sign                                 |
| -> zero-crossing tremor frequency estimate                               |
| -> RMS tremor magnitude                                                   |
| -> f_motor = k_factor * f_tremor                                          |
| -> opposing motor map (DORSAL/VOLAR/RADIAL/ULNAR)                        |
| -> MX1508 drives N20 motors with bounded intensity                        |
| -> telemetry TX to Node B                                                 |
| Receives config updates from Node B via 433 RX                            |
| Safety paths: clamp intensity + forced OFF mode                           |
+--------------------------------------------------------------------------+
```

## Packet Direction
- B -> A: `mode`, `k_factor`, `intensity_limit`
- A -> B: `f_tremor_hz`, `tremor_magnitude`, `axis`, `axis_sign`, `motor_id`, `f_motor_hz`, `k_factor`, `mode`
