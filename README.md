# Raspberry Pi Pico 2 Air Quality Event Monitor

> A MicroPython environmental event detector that learns a local baseline, identifies meaningful changes in humidity and gas resistance, and communicates system state through an OLED, LEDs, a buzzer, and serial telemetry.

<p align="center">
  <img src="docs%3A/normal-state.jpg" width="49%" alt="Prototype in the normal state with the green LED active" />
  <img src="docs%3A/alert-state.jpg" width="49%" alt="Prototype in the alert state with the red LED active" />
</p>

<p align="center"><em>Physical prototype operating in NORMAL and ALERT states.</em></p>

## Project Overview

This project explores how a small embedded system can turn raw environmental measurements into clear, stable, and actionable feedback. A Raspberry Pi Pico 2 reads temperature, humidity, pressure, and gas resistance from a BME688, establishes a baseline for the current room, and then detects relative changes rather than relying on fixed absolute values.

The firmware is organized around a state machine with threshold precedence, hysteresis, timed recovery, manual recalibration, and communication-error handling. This design prevents noisy readings near a threshold from causing rapid state changes and makes the system behavior easy to observe through both hardware outputs and serial logs.

> [!NOTE]
> This is a baseline-relative environmental event monitor, not a calibrated air-quality index, pollutant analyzer, smoke detector, or life-safety device. The BME688 gas-resistance reading is used to detect change; it is not presented as a direct concentration of a specific gas.

## At a Glance

| Area | Implementation |
|---|---|
| Platform | Raspberry Pi Pico 2 running MicroPython |
| Environmental sensor | BME688 over hardware I2C at address `0x77` |
| User interface | 128×64 SSD1306 OLED, three LEDs, active buzzer, and serial output |
| Detection method | Absolute percentage change from calibrated humidity and gas-resistance baselines |
| Stability controls | Separate entry/recovery thresholds plus a five-second recovery window |
| User control | Active-low push button with a one-second hold for recalibration |
| Fault behavior | Automatic sensor retry, tolerant OLED updates, and safe output cleanup on shutdown |

## Key Features

- Samples temperature, humidity, pressure, and gas resistance approximately once per second.
- Builds a local humidity and gas baseline from 15 startup samples.
- Prioritizes strong events over moderate events when both conditions are present.
- Uses lower recovery thresholds and a continuous stability timer to reduce state flicker.
- Displays the state, temperature, humidity, and largest relative change on the OLED.
- Maps each state to recognizable LED and buzzer feedback.
- Repeats a two-beep warning every three seconds while an alert remains active.
- Supports in-place recalibration without restarting the Pico.
- Retries BME688 read failures and continues monitoring after OLED write failures.
- Clears the LEDs, buzzer, and OLED when the program is stopped.

## System Behavior

1. **Initialize hardware.** The Pico configures the two I2C interfaces, GPIO outputs, buzzer, OLED, and recalibration button.
2. **Calibrate the room baseline.** The firmware averages positive humidity and gas-resistance values from 15 readings collected at one-second intervals.
3. **Measure continuously.** Each new sensor reading is compared with the stored baseline using absolute percentage change.
4. **Classify the event.** Alert thresholds are evaluated first, followed by warning thresholds and recovery conditions.
5. **Communicate state.** LEDs and the buzzer update when the state changes; the OLED and serial console update every successful sample.
6. **Recover deliberately.** After an event, both measurements must remain below their recovery thresholds for five seconds before the system returns to `NORMAL`.

### Detection Thresholds

| Decision level | Gas-resistance change | Humidity change | Result |
|---|---:|---:|---|
| Alert | `≥ 20%` | `≥ 12%` | Enter `ALERT` if either condition is true |
| Warning | `≥ 8%` | `≥ 5%` | Enter `SPIKE_DETECTED` if either condition is true |
| Stable recovery | `< 5%` | `< 3%` | Both conditions must remain true for five seconds |

Alert evaluation has precedence over warning evaluation. Temperature and pressure are displayed and logged, but they do not currently drive state transitions.

### State Outputs

| State | Meaning | Hardware behavior |
|---|---|---|
| `CALIBRATING` | Learning the current room baseline | Yellow LED; buzzer off |
| `NORMAL` | Humidity and gas resistance are close to baseline | Green LED; buzzer off |
| `SPIKE_DETECTED` | A moderate environmental change is present | Yellow LED; buzzer off |
| `ALERT` | A strong environmental change is present | Red LED; two beeps on entry and every three seconds |
| `RECOVERY` | Readings are stabilizing after an event | Green and yellow LEDs; buzzer off |
| `ERROR` | A BME688 sensor read failed | Red LED; buzzer off; retry after one second |

An OLED write error is logged without moving the state machine into `ERROR`; monitoring continues whenever the sensor read succeeds.

## State-Machine Design

The simplified view shows the user-facing behavior. The editable source is available in [PlantUML format](docs%3A/state_machine_simple.puml).

![Simplified air quality monitor state machine](docs%3A/state_machine_simple.png)

<details>
<summary><strong>View the detailed runtime control flow</strong></summary>

The detailed flow includes initialization, calibration, threshold precedence, recovery timing, manual recalibration, sensor retry, OLED error tolerance, serial reporting, and safe shutdown. See the [PlantUML source](docs%3A/state_machine.puml).

![Detailed air quality monitor runtime control flow](docs%3A/state_machine.png)

</details>

## Hardware Architecture

The prototype separates the BME688 and OLED onto different buses. The sensor uses hardware I2C at 100 kHz, while the display uses a conservative 10 kHz `SoftI2C` connection after higher-speed display communication proved unreliable during debugging.

![Annotated prototype wiring](docs%3A/Wiring_diagram.png)

### Components

| Component | Role |
|---|---|
| Raspberry Pi Pico 2 | Runs the monitoring, state-machine, display, and output logic |
| BME688 | Measures temperature, humidity, pressure, and gas resistance |
| SSD1306 OLED | Displays current state and live measurements |
| Green LED | Indicates normal operation |
| Yellow LED | Indicates calibration or a moderate event |
| Red LED | Indicates an alert or sensor-read error |
| Active buzzer | Provides the audible alert pattern |
| Push button | Requests manual baseline recalibration |
| Three 220 Ω resistors | Limit LED current |
| Breadboard and jumper wires | Support the physical prototype |

### Wiring Reference

| Component | Pico 2 connection | Notes |
|---|---:|---|
| BME688 SDA | GP16 | Hardware `I2C(0)` data |
| BME688 SCL | GP17 | Hardware `I2C(0)` clock |
| BME688 VIN/VCC | 3V3 OUT | Sensor power |
| BME688 GND | GND | Common ground |
| OLED SDA | GP18 | `SoftI2C` data |
| OLED SCL | GP19 | `SoftI2C` clock |
| OLED VCC | 3V3 OUT | Display power |
| OLED GND | GND | Common ground |
| Green LED | GP10 | Through a 220 Ω resistor |
| Yellow LED | GP11 | Through a 220 Ω resistor |
| Red LED | GP12 | Through a 220 Ω resistor |
| Active buzzer | GP14 | Positive pin; negative pin to GND |
| Recalibration button | GP5 | Other side to GND; internal pull-up enabled |

## Software Architecture

The application uses a small, intentionally direct MicroPython structure:

| File | Responsibility |
|---|---|
| [`src:/air_quality_monitor.py`](src%3A/air_quality_monitor.py) | Hardware setup, calibration, state decisions, output control, retry logic, and the main monitoring loop |
| [`src:/bme680.py`](src%3A/bme680.py) | BME680/BME688 I2C sensor driver and compensation calculations |
| [`src:/ssd1306.py`](src%3A/ssd1306.py) | SSD1306 framebuffer and I2C/SPI display driver |
| [`notes:/debugging-notes.md`](notes%3A/debugging-notes.md) | Hardware and MicroPython debugging observations |
| [`data:/sample_test.csv`](data%3A/sample_test.csv) | Schema reserved for future automated sample logging |

The main firmware remains a single cooperative loop, which is appropriate for this prototype and keeps state transitions easy to trace. Sensor acquisition, decision logic, UI updates, and timing are separated into functions so each responsibility can be inspected independently.

## Getting Started

### Prerequisites

- Raspberry Pi Pico 2 with a compatible MicroPython firmware installed
- Thonny or another MicroPython-capable editor/uploader
- Hardware listed in the component table
- A USB data cable

### Deploy to the Pico

1. Assemble the circuit using the wiring table and annotated wiring image.
2. Connect the Pico 2 and select its MicroPython interpreter in Thonny.
3. Upload these files to the Pico filesystem under the indicated names:

   - [`src:/bme680.py`](src%3A/bme680.py) as `bme680.py`
   - [`src:/ssd1306.py`](src%3A/ssd1306.py) as `ssd1306.py`
   - [`src:/air_quality_monitor.py`](src%3A/air_quality_monitor.py) as `air_quality_monitor.py`

4. Run `air_quality_monitor.py` from Thonny. To launch automatically on boot, save the application file as `main.py` after validating the hardware setup.
5. Keep the air around the BME688 stable during the initial 15-sample calibration period.

The startup log should show the detected I2C devices. This build expects the BME688 at `0x77` and the OLED at `0x3C`.

### Recalibrate

Hold the GP5 button for approximately one second. The yellow LED and OLED indicate recalibration while the system collects a fresh set of 15 baseline samples. Keep the surrounding air stable until monitoring resumes.

## Validation and Recorded Results

A controlled humidity event was introduced after calibrating the prototype in room conditions. The serial captures record the complete response path from normal operation into warning and alert states, followed by de-escalation and recovery.

| Observed stage | Humidity change | Gas change | State/result |
|---|---:|---:|---|
| Baseline conditions | `0.67%` | `0.00%` | `NORMAL` |
| Initial response | `7.31%` | `0.00%` | Transition to `SPIKE_DETECTED` |
| Alert-triggering sample | `20.26%` | `0.00%` | Transition to `ALERT` |
| Event decay | `10.72%` | `0.00%` | De-escalation from `ALERT` to `SPIKE_DETECTED` |
| Stable reading | `2.77%` | `0.00%` | Transition into `RECOVERY` |

The unchanged gas-resistance percentage in these captures shows that the recorded event path was driven by humidity. The observed transitions align with the configured 5% warning, 12% alert, and 3% recovery humidity thresholds.

Recorded evidence:

- [Initial `NORMAL → SPIKE_DETECTED → ALERT` response](docs%3A/Terminal_State_transitions.png/First%20responce.png)
- [`ALERT → SPIKE_DETECTED` de-escalation](docs%3A/Terminal_State_transitions.png/At%20the%20top.png)
- [`SPIKE_DETECTED → RECOVERY` transition](docs%3A/Terminal_State_transitions.png/Recovery.png)

The current CSV contains the intended logging columns but no captured rows; the results above come directly from the checked-in terminal screenshots.

## Engineering Decisions and Lessons

- **Baseline-relative detection:** Adapts the prototype to its local environment and makes controlled changes easy to demonstrate.
- **Threshold precedence:** Strong changes enter `ALERT` immediately instead of being temporarily classified as warnings.
- **Hysteresis and timed recovery:** Lower exit thresholds plus a five-second stability requirement reduce oscillation near state boundaries.
- **Separate I2C strategies:** Hardware I2C provides reliable sensor access, while low-speed `SoftI2C` resolved OLED timeout issues on the tested wiring.
- **State-driven outputs:** Centralizing LED and buzzer behavior makes transitions predictable and prevents stale outputs.
- **Safe cleanup:** The `finally` block turns off hardware outputs and clears the OLED after a stop request.
- **Observable firmware:** Serial telemetry and state-change messages made threshold tuning and hardware debugging practical.

## Current Limitations

- The device detects relative environmental changes; it does not calculate a standardized AQI or identify individual pollutants.
- Baselines are stored only in memory and must be rebuilt after a restart.
- The calibration average assumes at least one valid humidity and gas sample.
- The firmware uses a blocking cooperative loop rather than interrupts or scheduled tasks.
- Automated CSV logging and long-duration repeatability testing are not yet implemented.
- Breadboard wiring is suitable for prototyping but not for unattended or safety-critical deployment.

## Future Improvements

- Persist calibration data and configuration in non-volatile storage.
- Add timestamped CSV logging and graph humidity/gas changes over time.
- Introduce median filtering or rolling statistics for additional noise resistance.
- Add automated tests for threshold boundaries and recovery timing.
- Build a compact PCB or enclosed version of the prototype.
- Port the firmware to the Pico C/C++ SDK or separate work into FreeRTOS tasks.
- Use a Pico 2 W for a wireless dashboard, notifications, and remote history.

## Skills Demonstrated

MicroPython · Raspberry Pi Pico 2 · Embedded state machines · I2C and GPIO · Sensor integration · OLED UI design · Baseline calibration · Hysteresis · Fault handling · Hardware debugging · PlantUML documentation
