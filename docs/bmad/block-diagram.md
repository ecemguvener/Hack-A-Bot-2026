# Block Diagram
> Keep this on one page. While talking, literally point at boxes so judges can follow fast.

```text
+----------------------------------------------------+
| Node B: Base Pico (Bridge + Config + UI Forwarder) |
|----------------------------------------------------|
| nRF24 RX/TX                                        |
| Config manager: mode, k_factor, intensity_limit    |
| PC link: WebSocket/HTTP/TCP                        |
| Optional OLED status                               |
+--------------------------+-------------------------+
                           |
                           | nRF24 telemetry/config
                           v
+-------------------------------------------------------------------+
| Node A: VibraARM Glove Pico                                       |
|-------------------------------------------------------------------|
| BMI160 @ 100 Hz -> rolling window (1-2 s)                         |
| -> dominant axis/sign + RMS magnitude                             |
| -> filtered dominant axis -> zero-crossing frequency estimate     |
| -> f_motor = k_factor * f_tremor                                  |
| -> opposing motor selection (axis/sign map)                       |
| -> N20 motor drive (bounded duty/frequency)                       |
| -> telemetry packet TX                                             |
| RF/IMU fault checks -> safe fallback                              |
+-------------------------------------------------------------------+
```

## Packet Direction
- B -> A: `mode`, `k_factor`, `intensity_limit`, overrides/heartbeat
- A -> B: `timestamp`, `f_tremor`, `magnitude`, `axis`, `motor_id`, `f_motor`, `mode`, `k_factor`, fault flags
