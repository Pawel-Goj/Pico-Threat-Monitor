import time
from machine import Pin, I2C
import random
import ssd1306

time.sleep(0.1)

# SCL on GP7 and SDA on GP10 require I2C block 1
i2c = I2C(1, scl=Pin(7), sda=Pin(10), freq=400000)

oled = ssd1306.SSD1306_I2C(128, 64, i2c)

led_green = Pin(1, Pin.OUT)
led_yellow = Pin(2, Pin.OUT)
led_red = Pin(3, Pin.OUT)

haptic = Pin(5, Pin.OUT)

button = Pin(15, Pin.IN, Pin.PULL_DOWN)

blocked_list = []

def update_screen(status_text, val_text):
    oled.fill(0)
    oled.text("SENTRY-P v1.0", 0, 0, 1)
    oled.text("----------------", 0, 10, 1)
    oled.text("Status:", 0, 25, 1)
    oled.text(status_text, 0, 35, 1)
    oled.text(f"Val: {val_text}", 0, 50, 1)
    oled.show()

def startup():
    print("Running Sentry-P hardware self-test...")
    update_screen("BOOTING...", "TESTING...")
    led_green(0); led_yellow(0); led_red(0); haptic(0)

    for pin in [led_green, led_yellow, led_red]:
        pin(1)
        time.sleep_ms(100)
        pin(0)
        time.sleep_ms(75)

    update_screen("IDLE / READY", "---")
    print("Self-test complete. Entering main loop")

def trigger_haptic(duration_ms):
    haptic(1)
    time.sleep_ms(duration_ms)
    haptic(0)

startup()

while True:
    led_green(1)
    update_screen("SCANNING...", "WAITING")
    print("\nScanning subnet... waiting for event")

    time.sleep(5)
    led_green(0)

    threat_value = random.randint(1, 100)
    print(f"Event generated. Value: {threat_value}")
    if threat_value in blocked_list:
        print(f"-> Threat {threat_value} is already blocke. Ignoring.")
        update_screen("IGN (BLOCKED)", str(threat_value))
        time.sleep(2)
        continue

    if threat_value % 2 == 0:
        status_msg = "LOCAL ALERT"
        print("-> Status: LOCAL ANOMALY DETECTED")
        led_yellow(1)
        trigger_haptic(200)
    else:
        status_msg = "EXT THREAT"
        print("-> Status: EXTERNAL THREAT DETECTED")
        led_red(1)
        trigger_haptic(600)

    update_screen(status_msg, str(threat_value))

    start_time = time.ticks_ms()
    action_taken = False

    last_button_state = button.value()

    while time.ticks_diff(time.ticks_ms(), start_time) < 3000:
        current_button_state = button.value()

        if last_button_state == 0 and current_button_state == 1:
            blocked_list.append(threat_value)
            print(f"--> ACTION: Threat {threat_value} BLOCKED and logged.")
            update_screen("BLOCKED.", str(threat_value))

            trigger_haptic(100)
            time.sleep_ms(150)
            trigger_haptic(100)

            action_taken = True

            while button.value() == 0:
                time.sleep_ms(50)

            time.sleep(1)
            break
        time.sleep_ms(50)

    led_yellow(0)
    led_red(0)