# Wiring Diagram (Reference)
> Keep this file synced with your real pin map in code.

Note: keep final pin map consistent in firmware and this doc.

## Node A (VibraARM Glove Pico)

### BMI160 (I2C)
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

### N20 Motor Drive (required driver transistor/MOSFET stage)
- PWM/CTRL pin from Pico -> GP15 (example)
- Driver input <- GP15
- Driver output -> N20 motor terminals
- Motor supply -> regulated external rail
- Flyback protection required (if not integrated in driver)
- Common GND between Pico, driver, and motor supply

## Node B (Base Pico)

### nRF24L01+ (SPI)
- VCC -> 3V3
- GND -> GND
- CE  -> GP20
- CSN -> GP17
- SCK -> GP18
- MOSI-> GP19
- MISO-> GP16

### Optional Controls (if used on base)
- Joystick VRx -> GP26
- Joystick VRy -> GP27
- Joystick SW  -> GP22
- OLED SDA/SCL -> GP4/GP5

## Power Notes
> Most late failures are power-related. Test motors and radios together early.
- Do not power N20 directly from Pico pin.
- Isolate noisy motor supply from logic rail as much as possible.
- Use buck converter for stable rails.
- All grounds must be common.
