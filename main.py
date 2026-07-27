import time
from machine import Pin, I2C
import random
import ssd1306

time.sleep(0.1)

i2c = I2C(1, scl=Pin(7), sda=Pin(10), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

led_green = Pin(1, Pin.OUT)
led_yellow = Pin(2, Pin.OUT)
led_red = Pin(3, Pin.OUT)
haptic = Pin(5, Pin.OUT)

btn_up = Pin(13, Pin.IN, Pin.PULL_DOWN)
btn_down = Pin(14, Pin.IN, Pin.PULL_DOWN)
btn_select = Pin(15, Pin.IN, Pin.PULL_DOWN)

TAB_SCAN = 0
TAB_HISTORY = 1
TAB_NOTIFS = 2
current_tab = TAB_SCAN

scan_status_text = "READY"
scan_val_text = "---"

blocked_list = []
history_log = [] 
missed_alerts = [] 

scan_state = "IDLE"
scan_timer = 0
active_threat_val = 0
active_threat_type = ""

def update_screen():
    oled.fill(0)
    if current_tab == TAB_SCAN:
        oled.text("SENTRY-P: SCAN", 0, 0, 1)
        oled.text(f"St: {scan_status_text}", 0, 16, 1)
        oled.text(f"Val: {scan_val_text}", 0, 32, 1)
        oled.text("[1] < SCAN >", 0, 52, 1)
        
    elif current_tab == TAB_HISTORY:
        oled.text("SENTRY-P: HIST", 0, 0, 1)
        if len(history_log) > 0:
            latest = history_log[-1]
            oled.text(f"L:V{latest['val']} {latest['action']}", 0, 20, 1)
        else:
            oled.text("No history yet.", 0, 20, 1)
        oled.text("[2] < HIST >", 0, 52, 1)
        
    elif current_tab == TAB_NOTIFS:
        oled.text("SENTRY-P: NOTIF", 0, 0, 1)
        oled.text(f"Pend: {len(missed_alerts)} alerts", 0, 24, 1)
        oled.text("[3] < NOTIF >", 0, 52, 1)
    oled.show()

def draw_centered_text(text, y):
    screen_width = 128
    char_width = 8
    text_width = len(text) * char_width
    x = max(0, (screen_width - text_width) // 2)
    oled.text(text, x, y, 1)

def show_welcome_screen():
    oled.fill(0)
    draw_centered_text("SENTRY-P", 16)
    draw_centered_text("v1.1", 32)
    draw_centered_text("CENTIPEDE.NET", 52)
    oled.show()
    time.sleep(3)

def startup():
    print("Running Sentry-P hardware self-test...")
    global scan_status_text, scan_val_text
    scan_status_text = "BOOT..."
    scan_val_text = "TEST"
    update_screen()
    
    led_green(0); led_yellow(0); led_red(0); haptic(0)
    for pin in [led_green, led_yellow, led_red]:
        pin(1)
        time.sleep_ms(100)
        pin(0)
        time.sleep_ms(75)
        time.sleep(1)

    scan_status_text = "READY"
    scan_val_text = "---"
    update_screen()

    print("Self-test complete. Entering main loop.")

def trigger_haptic(duration_ms):
    haptic(1)
    time.sleep_ms(duration_ms)
    haptic(0)

def handle_threat_response(threat_val, threat_type, allow_timeout=True, timeout_ms=4000):
    print(f"-> Opening response menu for Threat {threat_val} ({threat_type})")
    actions = ["IGN", "WRN", "BLK"]
    action_labels = ["IGN (Ignore)", "WRN (Warn)", "BLK (Block)"]
    selected_index = 0
    
    def draw_action_menu():
        oled.fill(0)
        oled.text(f"THR:{threat_type} V:{threat_val}", 0, 0, 1)
        oled.text("Resp?", 0, 16, 1)
        oled.text(f"> {action_labels[selected_index]}", 0, 32, 1)
        oled.text("UP/DN OK:Sel", 0, 52, 1)
        oled.show()

    draw_action_menu()
    time.sleep(0.3)
    menu_start_time = time.ticks_ms()

    while True:
        current_time = time.ticks_ms()
        # Timeout only applies if allow_timeout is True
        if allow_timeout and time.ticks_diff(current_time, menu_start_time) > timeout_ms:
            print("-> Response window timed out. Moving on.")
            missed_alerts.append({"val": threat_val, "type": threat_type})
            led_yellow(0)
            led_red(0)
            return False

        if btn_up.value():
            selected_index = (selected_index - 1) % len(actions)
            print(f"Menu selection changed: {action_labels[selected_index]}")
            draw_action_menu()
            trigger_haptic(30)
            allow_timeout = False  # Disable timeout completely once user interacts with any button
            while btn_up.value():
                time.sleep_ms(50)
            time.sleep(0.15)
        elif btn_down.value():
            selected_index = (selected_index + 1) % len(actions)
            print(f"Menu selection changed: {action_labels[selected_index]}")
            draw_action_menu()
            trigger_haptic(30)
            allow_timeout = False  # Disable timeout completely once user interacts with any button
            while btn_down.value():
                time.sleep_ms(50)
            time.sleep(0.15)
        elif btn_select.value():
            chosen_action = actions[selected_index]
            trigger_haptic(80)
            
            action_code = "IGN"
            if chosen_action == "BLK":
                action_code = "BLOCK"
                if threat_val not in blocked_list:
                    blocked_list.append(threat_val)
            elif chosen_action == "WRN":
                action_code = "WARN"
            
            history_log.append({"val": threat_val, "action": action_code})
            print(f"--> ACTION EXECUTED: {action_code} on threat {threat_val}")
            
            oled.fill(0)
            oled.text("APPLIED:", 0, 16, 1)
            oled.text(f"-> {action_code}", 0, 32, 1)
            oled.show()
            time.sleep(1)
            
            while btn_select.value():
                time.sleep_ms(50)
            
            led_yellow(0)
            led_red(0)
            return True
        time.sleep_ms(20)

show_welcome_screen()
startup()
last_scan_time = time.ticks_ms()

while True:
    current_time = time.ticks_ms()
    
    if btn_up.value():
        current_tab = (current_tab - 1) % 3
        print(f"Switched tab to index: {current_tab}")
        trigger_haptic(40)
        update_screen()
        while btn_up.value():
            time.sleep_ms(50)
        time.sleep(0.15)
    elif btn_down.value():
        current_tab = (current_tab + 1) % 3
        print(f"Switched tab to index: {current_tab}")
        trigger_haptic(40)
        update_screen()
        while btn_down.value():
            time.sleep_ms(50)
        time.sleep(0.15)

    if current_tab == TAB_NOTIFS and btn_select.value():
        print("Opening Notifications inbox...")
        trigger_haptic(50)
        while btn_select.value():
            time.sleep_ms(50)
        
        if len(missed_alerts) > 0:
            alert = missed_alerts.pop(0)
            print(f"Retrieved alert from queue: {alert}")
            handle_threat_response(alert['val'], alert['type'], allow_timeout=False)
        else:
            print("Notifications queue is empty.")
            oled.fill(0)
            oled.text("NOTIFICATIONS", 0, 16, 1)
            oled.text("Queue empty.", 0, 32, 1)
            oled.show()
            time.sleep(1.5)
        update_screen()

    if scan_state == "IDLE":
        if time.ticks_diff(current_time, last_scan_time) > 6000:
            last_scan_time = current_time
            scan_status_text = "SCANNING"
            scan_val_text = "..."
            print("\nScanning subnet...")
            update_screen()
            led_green(1)
            scan_timer = current_time
            scan_state = "WAITING_SCAN"

    elif scan_state == "WAITING_SCAN":
        if time.ticks_diff(current_time, scan_timer) > 2000:
            led_green(0)
            threat_value = random.randint(1, 100)
            scan_val_text = str(threat_value)
            print(f"Event generated. Value: {threat_value}")
            
            if threat_value in blocked_list:
                scan_status_text = "BLOCKED"
                print(f"-> Threat {threat_value} is already blocked. Ignoring.")
                update_screen()
                scan_state = "IDLE"
                last_scan_time = current_time
                continue

            is_local = (threat_value % 2 == 0)
            threat_type = "LOCAL" if is_local else "EXT"
            scan_status_text = f"{threat_type} ALERT"
            print(f"-> Status: {threat_type} THREAT DETECTED")
            
            if is_local:
                led_yellow(1)
                trigger_haptic(200)
            else:
                led_red(1)
                trigger_haptic(500)
                
            update_screen()
            
            if current_tab == TAB_SCAN:
                active_threat_val = threat_value
                active_threat_type = threat_type
                scan_timer = current_time
                scan_state = "PROMPT_USER"
            else:
                print("-> User on different tab. Alert queued directly to notifications.")
                missed_alerts.append({"val": threat_value, "type": threat_type})
                led_yellow(0)
                led_red(0)
                scan_status_text = "READY"
                scan_state = "IDLE"
                last_scan_time = current_time

    elif scan_state == "PROMPT_USER":
        handle_threat_response(active_threat_val, active_threat_type, allow_timeout=True, timeout_ms=4000)
        scan_status_text = "READY"
        scan_state = "IDLE"
        last_scan_time = current_time
        update_screen()

    time.sleep_ms(20)
