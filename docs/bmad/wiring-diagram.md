# Wiring Diagram (Reference)

Note: Confirm exact pin choices on your final board; this is a stable starting map.

## Node A (Device Pico)

### BMI160 (I2C)
- VCC -> 3V3
- GND -> GND
- SDA -> GP4
- SCL -> GP5

### Actuation Output (choose one path)
1) Direct haptic motor driver signal
- PWM/CTRL -> GP16
- Driver power -> external regulated rail
- Common ground with Pico

2) Servo proxy via PCA9685
- PCA9685 VCC -> 3V3 (logic)
- PCA9685 GND -> GND
- PCA9685 SDA -> GP4
- PCA9685 SCL -> GP5
- Servo signal -> PCA9685 CH0/CH1
- Servo power -> dedicated 5V rail (not Pico 3V3)

### nRF24L01+ (SPI)
- VCC -> 3V3
- GND -> GND
- CE  -> GP20
- CSN -> GP17
- SCK -> GP18
- MOSI-> GP19
- MISO-> GP16 (if GP16 used, remap either CE/IRQ/CTRL)

## Node B (Companion Pico)

### Joystick
- VCC -> 3V3
- GND -> GND
- VRx -> GP26 (ADC0)
- VRy -> GP27 (ADC1)
- SW  -> GP22

### OLED 0.96" (I2C)
- VCC -> 3V3
- GND -> GND
- SDA -> GP4
- SCL -> GP5

### nRF24L01+ (SPI)
- VCC -> 3V3
- GND -> GND
- CE  -> GP20
- CSN -> GP17
- SCK -> GP18
- MOSI-> GP19
- MISO-> GP16

## Power Notes
- Use LM2596 for stable rails when actuators are used.
- Keep radio + logic rails clean; avoid sharing noisy motor rails directly.
- Mandatory: all grounds common between Pico, radio, sensors, and drivers.
