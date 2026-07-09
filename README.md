# Raspberry Pi Pico 2 Air Quality Event Monitor

A MicroPython-based environmental monitoring system built with a Raspberry Pi Pico 2 and BME688 sensor. The system measures temperature, humidity, pressure, and gas resistance, then compares live readings against a calibrated baseline to detect environmental changes.

The project uses a state-machine design with visual and audible feedback through an OLED display, green/yellow/red LEDs, a buzzer, and a manual recalibration button.

## Demo Photos

### Full Prototype
<img width="320" height="240" alt="project-overview" src="https://github.com/user-attachments/assets/d057e4a6-e7a5-4fd7-8f56-00f5ff7f2b99" />

### Wiring Diagram
<img width="820" height="615" alt="Wiring_diagram" src="https://github.com/user-attachments/assets/f6dd3570-4726-43ec-8731-835ccbb6ee2d" />

### State Machine
<img width="598" height="962" alt="state_machine" src="https://github.com/user-attachments/assets/8ff002b1-8ac9-4804-86f2-3552f6361ccc" />

### Normal State
<img width="320" height="240" alt="normal-state" src="https://github.com/user-attachments/assets/666656e4-49c3-4216-bc97-4111c5afbb28" />

### Alert State
<img width="320" height="240" alt="alert-state" src="https://github.com/user-attachments/assets/42fae83d-2762-468b-82c1-bcbd0617b3df" />

## Features

- BME688 environmental sensing over I2C
- Temperature, humidity, pressure, and gas-resistance readings
- Baseline calibration at startup
- Manual recalibration button
- OLED display for live readings and current state
- Green/yellow/red LED indicators
- Periodic buzzer alert during unstable air conditions
- Hysteresis-based thresholds to reduce state flickering
- Recovery state before returning to normal
- Basic error handling for sensor/OLED communication issues

## Hardware Used

| Component | Purpose |
|---|---|
| Raspberry Pi Pico 2 | Main microcontroller |
| BME688 sensor | Environmental sensing |
| SSD1306 OLED display | Live data and state display |
| Green LED | Normal state indicator |
| Yellow LED | Spike detected / calibration indicator |
| Red LED | Alert / error indicator |
| Active buzzer | Audible alert |
| Push button | Manual recalibration input |
| 220Ω resistors | LED current limiting |
| Breadboard and jumper wires | Prototyping |

## Wiring Table

| Component | Pico 2 Connection | Purpose |
|---|---:|---|
| BME688 SDA | GP16 | I2C data line for environmental sensor |
| BME688 SCL | GP17 | I2C clock line for environmental sensor |
| BME688 VIN/VCC | 3V3 OUT | Sensor power |
| BME688 GND | GND | Sensor ground |
| OLED SDA | GP18 | I2C data line for display |
| OLED SCL | GP19 | I2C clock line for display |
| OLED VCC | 3V3 OUT | Display power |
| OLED GND | GND | Display ground |
| Green LED | GP10 | Normal state indicator |
| Yellow LED | GP11 | Spike detected / calibration indicator |
| Red LED | GP12 | Alert / error indicator |
| Buzzer + | GP14 | Audible alert output |
| Buzzer - | GND | Buzzer ground |
| Recalibration button | GP5 | Manual baseline recalibration input |
| Button other side | GND | Button ground |

## State Machine

The system uses the following states:

| State | Behavior |
|---|---|
| Calibrating | Collects baseline humidity and gas readings |
| Normal | Readings are close to baseline; green LED is on |
| Spike Detected | Moderate change detected; yellow LED is on |
| Alert | Strong change detected; red LED and buzzer activate |
| Recovery | Readings are stabilizing before returning to normal |
| Error | Sensor or OLED communication problem detected |

## How It Works

At startup, the system collects baseline readings from the BME688 sensor. During live monitoring, each new reading is compared to the baseline. If humidity or gas-resistance change exceeds warning thresholds, the system enters `SPIKE_DETECTED`. If the change exceeds alert thresholds, it enters `ALERT`.

The system uses hysteresis and a recovery timer so it does not rapidly switch between states when readings are near a threshold. A button allows the user to recalibrate the baseline without restarting the program.

## Test Results

A controlled test was performed by allowing the system to calibrate in normal room conditions, then introducing a humidity change near the sensor. The system transitioned from `NORMAL` to `SPIKE_DETECTED`, then to `ALERT`, and later moved through `RECOVERY` as the readings stabilized.

During one test, humidity change increased from less than 1% to over 20%, triggering the alert state. Gas resistance remained stable in this test, so the event was primarily humidity-driven.

## Challenges

Some of the main debugging challenges included:

- Choosing correct Pico GPIO pins for I2C communication
- Fixing library issues with the BME688 driver
- Debugging OLED timeouts and switching to a more reliable I2C setup
- Preventing LEDs and the buzzer from staying on after stopping the program
- Tuning thresholds so the system reacted clearly without flickering between states
- Adding recovery logic and manual recalibration

## Future Improvements

- Log sensor readings to a CSV file automatically
- Create graphs of humidity/gas change over time
- Add a case or 3D-printed enclosure
- Rebuild the project using the Pico C/C++ SDK
- Experiment with FreeRTOS tasks for sensing, display, and alerts
- Use a Pico 2 W for wireless dashboard or notifications

## Skills Demonstrated

- MicroPython
- Raspberry Pi Pico 2
- I2C communication
- GPIO input/output
- Sensor integration
- OLED display control
- State-machine design
- Baseline calibration
- Embedded debugging
- Hardware prototyping
