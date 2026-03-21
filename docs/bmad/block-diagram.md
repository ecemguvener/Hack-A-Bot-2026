# Block Diagram

```text
                 +-------------------------------------------+
                 |            Node B: Companion Pico         |
                 |-------------------------------------------|
                 | Joystick / Buttons -> Mode/Profile Select |
                 | OLED <- Telemetry + Link Status           |
                 | nRF24 TX/RX (Supervisor + Control)        |
                 +--------------------+----------------------+
                                      |
                                      | 2.4 GHz nRF24 packets
                                      v
+------------------------------------------------------------------------+
|                     Node A: Device/Wearable Pico                       |
|------------------------------------------------------------------------|
| BMI160 IMU -> Feature Extraction -> Adaptive Selector -> Actuation Out |
|                 |                   |                                   |
|                 +-> Telemetry ----->+                                   |
| RF Heartbeat Monitor -> Safe Fallback (neutral/minimum output)         |
+------------------------------------------------------------------------+
```

## Packet Direction
- B -> A: mode, profile, enable/disable assist, heartbeat
- A -> B: tremor amplitude proxy, smoothness, stability, actuator command, fault flags
