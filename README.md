# Pico Threat Monitor

An embedded MicroPython threat detection and anomaly monitoring system built for the Raspberry Pi Pico W. This project simulates network scanning, real-time alert dispatching, and interactive threat mitigation using physical peripherals.

## Features
* **Simulated Network Scanner:** Periodically cycles through status states and generates randomized threat payloads.
* **Multi-Tier Visual Feedback:** Independent LED indicators for operational status (Green), local anomalies (Yellow), and external threats (Red).
* **Haptic Alert System:** Provides tactile feedback via a vibrating motor during active threat events.
* **Interactive Threat Mitigation:** Features a dedicated hardware button with a timed response window to intercept, log, and auto-ignore specific threat vectors.
* **OLED Dashboard:** Real-time data visualization via an SSD1306 I2C display.

## Hardware Components
* Raspberry Pi Pico W
* SSD1306 OLED Display (128x64)
* 3x LEDs (Green, Yellow, Red)
* Haptic Motor / Buzzer
* Pushbutton (configured with Pull-Down logic)

## Wiring Pinout

| Component | Pico W Pin |
| :--- | :--- |
| OLED SCL | GP7 |
| OLED SDA | GP10 |
| Green LED | GP1 |
| Yellow LED | GP2 |
| Red LED | GP3 |
| Haptic Motor | GP5 |
| Block Button | GP15 |

## Getting Started
1. Open the included `diagram.json` in the [Wokwi Simulator](https://wokwi.com/).
2. Load `main.py` and the `ssd1306.py` driver into the environment.
3. Run the simulation to watch the live threat monitoring loop in action.
