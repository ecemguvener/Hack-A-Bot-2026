# test_motor.py
# Motor A (MX1508 H-bridge IN1/IN2) functional test for Pico 2
#
# Wiring:
#   IN1 -> GP10
#   IN2 -> GP11
#   Motor A output -> motor terminals
#   No ENA pin on MX1508; speed control via PWM on IN1/IN2
#
# Run on Pico connected to PC via USB (Thonny or mpremote).
# Each test prints PASS/FAIL and what the motor should be doing.

import time
from machine import Pin, PWM

# --- Pin config ---
IN1 = PWM(Pin(10))
IN2 = PWM(Pin(11))
IN1.freq(1000)
IN2.freq(1000)

# No ENA pin for MX1508


# --- Low-level helpers ---

def motor_forward(speed=1.0):
    """Forward at given speed (0.0 to 1.0)."""
    duty = int(speed * 65535)
    IN1.duty_u16(duty)
    IN2.duty_u16(0)

def motor_backward(speed=1.0):
    """Backward at given speed (0.0 to 1.0)."""
    duty = int(speed * 65535)
    IN1.duty_u16(0)
    IN2.duty_u16(duty)

def motor_stop():
    """Brake: both pins HIGH (active stop)."""
    IN1.duty_u16(65535)
    IN2.duty_u16(65535)

def motor_coast():
    """Coast: both pins LOW (free spin)."""
    IN1.duty_u16(0)
    IN2.duty_u16(0)


# --- Tests ---

def test_forward(duration=2.0):
    """Motor should spin in one direction for duration seconds."""
    print("\n[TEST] Forward")
    print(f"  -> Motor should spin FORWARD for {duration}s")
    motor_forward()
    time.sleep(duration)
    motor_stop()
    result = input("  Did the motor spin? (y/n): ").strip().lower()
    if result == 'y':
        print("  PASS")
        return True
    print("  FAIL")
    return False


def test_backward(duration=2.0):
    """Motor should spin in the opposite direction for duration seconds."""
    print("\n[TEST] Backward")
    print(f"  -> Motor should spin BACKWARD for {duration}s")
    motor_backward()
    time.sleep(duration)
    motor_stop()
    result = input("  Did the motor spin in reverse? (y/n): ").strip().lower()
    if result == 'y':
        print("  PASS")
        return True
    print("  FAIL")
    return False


def test_stop():
    """Motor should brake immediately after running."""
    print("\n[TEST] Stop (brake)")
    print("  -> Motor will run forward for 1s then brake")
    motor_forward()
    time.sleep(1.0)
    motor_stop()
    result = input("  Did the motor stop quickly (brake)? (y/n): ").strip().lower()
    if result == 'y':
        print("  PASS")
        return True
    print("  FAIL")
    return False


def test_coast():
    """Motor should coast (spin freely) after running."""
    print("\n[TEST] Coast (free spin)")
    print("  -> Motor will run forward for 1s then coast")
    motor_forward()
    time.sleep(1.0)
    motor_coast()
    result = input("  Did the motor coast (spin down slowly)? (y/n): ").strip().lower()
    if result == 'y':
        print("  PASS")
        return True
    print("  FAIL")
    return False


def test_direction_change():
    """Motor should reverse direction without stopping."""
    print("\n[TEST] Direction change (forward -> reverse)")
    print("  -> Forward 1.5s, then immediately reverse 1.5s")
    motor_forward()
    time.sleep(1.5)
    motor_backward()
    time.sleep(1.5)
    motor_stop()
    result = input("  Did the motor change direction? (y/n): ").strip().lower()
    if result == 'y':
        print("  PASS")
        return True
    print("  FAIL")
    return False


def test_speed_pwm():
    """
    PWM speed sweep test for MX1508.
    Sweeps from 10% to 100% duty cycle in steps.
    """
    print("\n[TEST] PWM speed sweep (MX1508)")
    print("  Sweeping speed 10% -> 100% -> 10%")

    for pct in list(range(10, 101, 10)) + list(range(100, 9, -10)):
        speed = pct / 100.0
        motor_forward(speed)
        print(f"    {pct}% speed", end="\r")
        time.sleep(0.4)

    motor_stop()

    result = input("\n  Did the motor speed change smoothly? (y/n): ").strip().lower()
    if result == 'y':
        print("  PASS")
        return True
    print("  FAIL")
    return False


def test_rapid_toggle(count=10):
    """Rapidly toggle forward/backward to stress-test the driver."""
    print(f"\n[TEST] Rapid direction toggle x{count}")
    print("  -> Toggling direction rapidly (100ms each)")
    for i in range(count):
        motor_forward()
        time.sleep(0.1)
        motor_backward()
        time.sleep(0.1)
    motor_stop()
    print("  -> Done. Check motor and driver board are not hot.")
    result = input("  Board and motor survived? (y/n): ").strip().lower()
    if result == 'y':
        print("  PASS")
        return True
    print("  FAIL")
    return False


# --- Run all tests ---

def run_all():
    print("=" * 40)
    print("  Motor Board Integration Test")
    print("  MX1508: IN1=GP10, IN2=GP11")
    print("=" * 40)

    results = {}
    results["forward"]          = test_forward()
    results["backward"]         = test_backward()
    results["stop"]             = test_stop()
    results["coast"]            = test_coast()
    results["direction_change"] = test_direction_change()
    results["speed_pwm"]        = test_speed_pwm()
    results["rapid_toggle"]     = test_rapid_toggle()

    motor_coast()  # safe final state

    print("\n" + "=" * 40)
    print("  Results Summary")
    print("=" * 40)
    for name, r in results.items():
        status = "PASS" if r else ("SKIP" if r is None else "FAIL")
        print(f"  {name:<20} {status}")
    print("=" * 40)


run_all()
