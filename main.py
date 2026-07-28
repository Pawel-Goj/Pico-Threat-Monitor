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

class Button:
    def __init__(self, pin):
        self.pin = pin
        self.last_state = False
        self.last_press_time = 0
        self.debounce_ms = 50

    def pressed(self):
        current = self.pin.value()
        now = time.ticks_ms()
        if current and not self.last_state:
            if time.ticks_diff(now, self.last_press_time) > self.debounce_ms:
                self.last_press_time = now
                self.last_state = current
                return True
        self.last_state = current
        return False
    
    def held(self):
        return self.pin.value()

btn_up = Button(Pin(13, Pin.IN, Pin.PULL_DOWN))
btn_down = Button(Pin(14, Pin.IN, Pin.PULL_DOWN))
btn_select = Button(Pin(15, Pin.IN, Pin.PULL_DOWN))

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

def haptic_pattern(pattern):
    patterns = {
        'click': [(50, 0)],
        'confirm': [(50, 100), (50, 0)],
        'alert': [(500, 0)],
        'error': [(30, 30), (30, 30), (30, 0)],
    }

    print(f"[HAPTIC] {pattern}")

    for on_time, off_time in patterns.get(pattern, [(50, 0)]):
        haptic(1)
        time.sleep_ms(on_time)
        haptic(0)
        if off_time > 0:
            time.sleep_ms(off_time)

def trigger_haptic(duration_ms):
    print(f"[HAPTIC] buzz {duration_ms}ms")
    haptic(1)
    time.sleep_ms(duration_ms)
    haptic(0)

class UIAnimator:
    def __init__(self):
        self.animation_active = False
        self.start_time = 0
        self.duration = 0
        self.from_value = 0
        self.to_value = 0
        self.current_value = 0
    
    def start(self, duration_ms, from_val, to_val):
        self.animation_active = True
        self.start_time = time.ticks_ms()
        self.duration = duration_ms
        self.from_value = from_val
        self.to_value = to_val

    def update(self):
        if not self.animation_active:
            return self.to_value
        elapsed = time.ticks_diff(time.ticks_ms(), self.start_time)
        progress = min(1.0, elapsed / self.duration)
        eased = progress * progress * (3 - 2 * progress)
        self.current_value = self.from_value + (self.to_value - self.from_value) * eased
        if progress >= 1.0:
            self.animation_active = False
        return self.current_value

def draw_centered_text(text, y):
    screen_width = 128
    char_width = 8
    text_width = len(text) * char_width
    x = max(0, (screen_width - text_width) // 2)
    oled.text(text, x, y, 1)

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

def boot_seq():
    print("[BOOT] Starting Sentry-P v1.2")

    oled.fill(0)
    draw_centered_text("SENTRY-P", 8)
    draw_centered_text("CENTIPEDE.NET", 40)
    oled.show()
    time.sleep(1.5)
    haptic_pattern('confirm')

    oled.fill(0)
    draw_centered_text("Booting...", 0)
    for dx in range(100):
        oled.pixel(14 + dx, 30, 1)
        oled.pixel(14 + dx, 37, 1)
    for dy in range(8):
        oled.pixel(14, 30 + dy, 1)
        oled.pixel(113, 30 + dy, 1)

# Animate loading bar fill
    for i in range(0, 20):
        for dx in range(i * 5):
            for dy in range(6):
                oled.pixel(15 + dx, 31 + dy, 1)
        oled.show()
        time.sleep_ms(50)

    haptic_pattern('click')
    print("[BOOT] system ready")
    time.sleep(0.3)

def show_welcome_screen():
    oled.fill(0)
    draw_centered_text("SENTRY-P", 16)
    draw_centered_text("v1.2", 32)
    draw_centered_text("CENTIPEDE.NET", 52)
    oled.show()
    time.sleep(2)

def startup():
    print("Running Sentry-P hardware self-test...")
    global scan_status_text, scan_val_text
    scan_status_text = "BOOT..."
    scan_val_text = "TEST"
    update_screen()
    
    led_green(0); led_yellow(0); led_red(0); haptic(0)

    for pin, name, pattern in [(led_green, 'GREEN', 'click'),
                (led_yellow, 'YELLOW', 'click'),
                (led_red, 'RED', 'click')]:
        pin(1)
        print(f"[TEST] LED {name} ON")
        haptic_pattern(pattern)
        time.sleep_ms(150)
        pin(0)
        print(f"[TEST] LED {name} OFF")
        time.sleep_ms(100)

    scan_status_text = "READY"
    scan_val_text = "---"
    update_screen()
    print("Self-test complete. Entering main loop.")

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
    time.sleep_ms(300) 
    menu_start_time = time.ticks_ms()

    while True:
        current_time = time.ticks_ms()
        if allow_timeout and time.ticks_diff(current_time, menu_start_time) > timeout_ms:
            print("-> Response window timed out. Moving on.")
            missed_alerts.append({"val": threat_val, "type": threat_type})
            led_yellow(0)
            led_red(0)
            haptic_pattern('error')
            return False

        if btn_up.pressed():
            selected_index = (selected_index - 1) % len(actions)
            print(f"menu selection changed: {action_labels[selected_index]}")
            draw_action_menu()
            haptic_pattern('click')
            allow_timeout = False

        elif btn_down.pressed():
            selected_index = (selected_index + 1) % len(actions)
            print(f"menu selection changed: {action_labels[selected_index]}")
            draw_action_menu()
            haptic_pattern('click')
            allow_timeout = False

        elif btn_select.pressed():
            chosen_action = actions[selected_index]
            haptic_pattern('confirm')
            
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
            time.sleep_ms(800) 
            
            while btn_select.pressed():
                time.sleep_ms(50) 
            
            led_yellow(0)
            led_red(0)
            return True
        time.sleep_ms(20) 

led_brightness = UIAnimator()
led_brightness.start(500, 0, 100)

boot_seq()
startup()
last_scan_time = time.ticks_ms()

while True:
    current_time = time.ticks_ms()
    
    if btn_up.pressed():
        current_tab = (current_tab - 1) % 3
        tab_names = ["SCAN", "HISTORY", "NOTIFS"]
        print(f"[NAV] tab: {tab_names[current_tab]}")
        haptic_pattern('click')
        update_screen()
        time.sleep_ms(100)

    elif btn_down.pressed():
        current_tab = (current_tab + 1) % 3
        tab_names = ["SCAN", "HISTORY", "NOTIFS"]
        print(f"[NAV] tab: {tab_names[current_tab]}")
        haptic_pattern('click')
        update_screen()
        time.sleep_ms(100)

    if current_tab == TAB_NOTIFS and btn_select.pressed():
        print("[NOTIF] opening inbox.")
        haptic_pattern('click')
        
        if len(missed_alerts) > 0:
            alert = missed_alerts.pop(0)
            print(f"[NOTIF] processing alert: {alert}")
            handle_threat_response(alert['val'], alert['type'], allow_timeout=False)
        else:
            print("[NOTIF] queue empty.")
            oled.fill(0)
            oled.text("NOTIFICATIONS", 16)
            oled.text("Queue empty.", 32)
            oled.show()
            time.sleep_ms(1200)
        update_screen()

    if scan_state == "IDLE":
        if time.ticks_diff(current_time, last_scan_time) > 6000:
            last_scan_time = current_time
            scan_status_text = "SCANNING"
            scan_val_text = "..."
            print("\n[SCAN] Scanning subnet...")
            update_screen()
            led_green(1)
            haptic_pattern('click')
            scan_timer = current_time
            scan_state = "WAITING_SCAN"

    elif scan_state == "WAITING_SCAN":
        if time.ticks_diff(current_time, scan_timer) > 2000:
            led_green(0)
            threat_value = random.randint(1, 100)
            scan_val_text = str(threat_value)
            print(f"[SCAN] Event generated. Value: {threat_value}")
            
            if threat_value in blocked_list:
                scan_status_text = "BLOCKED"
                print(f"[SCAN] Threat {threat_value} is already blocked. Ignoring.")
                haptic_pattern('click')
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
                haptic_pattern('alert')
            else:
                led_red(1)
                haptic_pattern('alert')
                
            update_screen()
            
            if current_tab == TAB_SCAN:
                active_threat_val = threat_value
                active_threat_type = threat_type
                scan_timer = current_time
                scan_state = "PROMPT_USER"
            else:
                print("[SCAN] User on different tab. Alert queued directly to notifications.")
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
