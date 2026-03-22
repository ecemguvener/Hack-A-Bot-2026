# Wiring Diagram (Reference)
> Keep this file synced with your real pin map in code.

Note: keep final pin map consistent in firmware and this doc.

## Node A (VibraARM Glove Pico)

### BMI160 (I2C)
- VCC -> 3V3
- GND -> GND
- SDA -> GP0
- SCL -> GP1

### 433 MHz TX (FS1000A) - telemetry to base
- VCC -> 3V3
- GND -> GND
- DATA -> GP10

### 433 MHz RX (XY-MK-5V) - config from base
- DATA output is 5V, must be level-shifted before Pico GPIO
- Level-shifted DATA -> GP11
- VCC -> external 5V (module dependent), GND common with Pico

### N20 Motor Drive (MX1508, 4 channels)
- Motor A (DORSAL): IN1 GP2, IN2 GP3
- Motor B (VOLAR):  IN1 GP4, IN2 GP5
- Motor C (RADIAL): IN1 GP6, IN2 GP7
- Motor D (ULNAR):  IN1 GP8, IN2 GP9
- MX1508 motor supply -> external rail
- Pico GND, driver GND, sensor GND, RF GND must be common

## Node B (Base Pico)

### 433 MHz RX (XY-MK-5V) - telemetry from glove
- DATA output is 5V, must be level-shifted before Pico GPIO
- Level-shifted DATA -> GP0
- GND -> GND (common)

### 433 MHz TX (FS1000A) - config to glove
- DATA -> GP2
- VCC -> 3V3
- GND -> GND

### USB
- Pico USB -> laptop for serial commands + bridge

## Power Notes
> Most late failures are power-related. Test motors and radios together early.
- Do not power N20 directly from Pico pin.
- Isolate noisy motor supply from logic rail as much as possible.
- Use buck converter for stable rails.
- All grounds must be common.
- Level-shift any 5V RF receiver output before Pico GPIO input.
