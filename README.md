# SENTRY-P v1.1

An asynchronous, non-blocking embedded security appliance and threat-simulation firmware built for the Raspberry Pi Pico W using MicroPython. SENTRY-P provides real-time telemetry, multi-modal hardware feedback, and an interactive tabbed UI to scan, triage, and log network anomalies.

---

## Technical Architecture & Core Updates (v1.1)

* **Asynchronous State Machine:** Replaced blocking execution paths with a non-blocking poll loop (`time.ticks_ms()`), allowing concurrent execution of subnet scans, hardware event polling, and debounced button handling without dropping frames or freezing.
* **Optimized Tabbed UI (128x64 SSD1306):** Employs I2C communication (`freq=400000`) to manage a multi-view state machine:
  1. **Scan View (`TAB_SCAN`):** Real-time telemetry displaying operational state (`READY`, `SCANNING`, `LOCAL/EXT ALERT`) and live threat vector values.
  2. **History View (`TAB_HISTORY`):** Persistent audit log tracking the latest triage action (`IGNORE`, `WARN`, `BLOCK`) and vector ID.
  3. **Notification View (`TAB_NOTIFS`):** FIFO background queue capturing unhandled asynchronous events (capable of buffering hundreds of queued background alerts while multitasking).
* **Dynamic Timeout Interruption Logic:** Implements fallback timeout protection (4000ms window) on active scan prompts that automatically routes ignored alerts to the background queue. Pressing any navigation input (`UP`, `DOWN`, `SELECT`) dynamically overrides and suspends the timeout timer until user triage is completed.
* **Multi-Modal Peripheral Integration:**
  * **Visual Status Array:** Independent GPIO-driven LED lines for operational state (Green), local anomalies (Yellow), and external threats (Red).
  * **Tactile Haptic Feedback:** Pulse-width / duration-mapped vibrational buzzer control for state changes and threat severities.
  * **Debounced Tactile Inputs:** Active-high pull-down button matrix (`Pin.PULL_DOWN`) with built-in software debounce delays.

---

## Hardware Pinout Configuration

| Component | MicroPython Pin | Interface / Protocol | Description |
| :--- | :--- | :--- | :--- |
| **OLED SCL** | `Pin(7)` | I2C (Bus 1) | I2C Serial Clock Line |
| **OLED SDA** | `Pin(10)` | I2C (Bus 1) | I2C Serial Data Line |
| **LED Green** | `Pin(1)` | GPIO (OUT) | Operational / Ready State |
| **LED Yellow** | `Pin(2)` | GPIO (OUT) | Local Threat Warning |
| **LED Red** | `Pin(3)` | GPIO (OUT) | External Threat Alert |
| **Haptic Motor** | `Pin(5)` | GPIO (OUT) | Tactile Feedback Actuator |
| **Button Up** | `Pin(13)` | GPIO (IN, PULL_DOWN) | Scroll Up / Tab Left |
| **Button Down** | `Pin(14)` | GPIO (IN, PULL_DOWN) | Scroll Down / Tab Right |
| **Button Select** | `Pin(15)` | GPIO (IN, PULL_DOWN) | Action Confirm / Inbox Access |

---

## Execution & Deployment

1. Configure the hardware circuit matching the pin mapping in `diagram.json` within the Wokwi simulator environment.
2. Flash the required dependencies (`ssd1306.py` display driver) alongside `main.py` to the target runtime.
3. Initialize execution to trigger the startup hardware self-test routine and enter the main non-blocking event loop.
