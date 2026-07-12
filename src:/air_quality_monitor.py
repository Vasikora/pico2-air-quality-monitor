from machine import Pin, I2C, SoftI2C
from bme680 import BME680_I2C
import ssd1306
import time


# =========================================================
# Configuration
# =========================================================

# Entering-state thresholds
GAS_WARNING_THRESHOLD = 8
GAS_ALERT_THRESHOLD = 20

HUMIDITY_WARNING_THRESHOLD = 5
HUMIDITY_ALERT_THRESHOLD = 12

# Lower thresholds used when returning to NORMAL.
# This prevents rapid switching between states.
GAS_RECOVERY_THRESHOLD = 5
HUMIDITY_RECOVERY_THRESHOLD = 3

# The readings must remain stable for this long
# before the system returns to NORMAL.
RECOVERY_TIME_MS = 5000

# Repeat the buzzer during ALERT every 3 seconds.
ALERT_BEEP_INTERVALS_MS = 3000

# Delay between normal sensor readings.
SAMPLE_INTERVAL_MS = 1000

CALIBRATION_SAMPLES = 15


# -----------------------------
# Pin setup
# -----------------------------

# BME688 sensor:
# SDA = GP16
# SCL = GP17
i2c_sensor = I2C(0, sda=Pin(16), scl=Pin(17), freq=100000)

# LEDs:
green_led = Pin(10, Pin.OUT)
yellow_led = Pin(11, Pin.OUT)
red_led = Pin(12, Pin.OUT)

bme = BME680_I2C(i2c=i2c_sensor, address=0x77)

# Active buzzer on GP14
buzzer = Pin(14, Pin.OUT)
buzzer.value(0)

#OLED setup
i2c_oled = SoftI2C( sda=Pin(18), scl=Pin(19), freq=10000, timeout=10000)

time.sleep(1)

oled_devices = i2c_oled.scan()
print( "OLED Devices:", ["0x{:02X}".format(device) for device in oled_devices])

if 0x3C not in oled_devices:
    raise RuntimeError("OLED not found. Check VCC, GND, SDA GP18, and SCL GP19.")

oled = ssd1306.SSD1306_I2C(128, 64, i2c_oled, addr=0x3C)

recalibrate_button = Pin(5, Pin.IN, Pin.PULL_UP)

# -----------------------------
# LED functions
# -----------------------------

def all_leds_off():
    green_led.value(0)
    yellow_led.value(0)
    red_led.value(0)


def set_leds(green, yellow, red):
    green_led.value(green)
    yellow_led.value(yellow)
    red_led.value(red)


def show_state(state):
    if state == "NORMAL":
        set_leds(1, 0, 0)
        buzzer_off()
        
    elif state == "SPIKE_DETECTED":
        set_leds(0, 1, 0)
        buzzer_off()
        
    elif state == "ALERT":
        set_leds(0, 0, 1)
        
    elif state == "RECOVERY":
        # Green and yellow together indicate recovery.
        set_leds(1, 1, 0)
        buzzer_off()   
        
    elif state == "CALIBRATING":
        set_leds(0, 1, 0)
        buzzer_off()
        
    elif state == "ERROR":
        set_leds(0, 0, 1)
        buzzer_off()
        
    else:
        all_leds_off()
        buzzer_off()


def buzzer_off():
    buzzer.value(0)


def short_beep(duration=0.15):
    buzzer.value(1)
    time.sleep(duration)
    buzzer.value(0)


def alert_beep():
    # Two short warning beeps
    for _ in range(2):
        buzzer.value(1)
        time.sleep(0.15)
        buzzer.value(0)
        time.sleep(0.1)
        
#------------------------------
#OLED Functions
#------------------------------

def oled_clear():
    oled.fill(0)
    oled.show()
    
def oled_message(line1="", line2="", line3="", line4=""):
    oled.fill(0)

    oled.text(str(line1)[:16], 0, 0)
    oled.text(str(line2)[:16], 0, 16)
    oled.text(str(line3)[:16], 0, 32)
    oled.text(str(line4)[:16], 0, 48)

    oled.show()


def update_oled(
    state,
    temp_c,
    humidity,
    gas_change,
    humidity_change):
    
    oled.fill(0)

    oled.text("AIR MONITOR", 0, 0)
    oled.text("State:" + state[:9], 0, 14)
    oled.text("Temp:{:.1f}C".format(temp_c), 0, 28)
    oled.text("Hum:{:.1f}%".format(humidity), 0, 40)
    
    
    event_change = max(gas_change, humidity_change)

    oled.text(
        "Change:{:.1f}%".format(event_change), 0, 52)
    oled.show()

def show_error_on_oled(message):
    try:
        oled.fill(0)
        oled.text("SYSTEM ERROR", 0,0)
        oled.text(str(message)[:16], 0, 20)
        oled.text("Retrying...", 0, 40)
        oled.show()
    except OSError:
        # If the OLED itself failed, do not crash again.
        pass


# -----------------------------
# Sensor functions
# -----------------------------

def read_sensor():
    temp_c = bme.temperature
    humidity = bme.humidity
    pressure = bme.pressure
    gas = bme.gas
    return temp_c, humidity, pressure, gas


def percent_change(current, baseline):
    if baseline == 0:
        return 0
    return abs(current - baseline) / baseline * 100


def calibrate(samples=15):
    print("Calibrating baseline...")
    print("Keep sensor still. Do not breathe on it yet.")

    show_state("CALIBRATING")
    
    oled_message("CALIBRATING", "Keep air still", "Please wait...", "")

    gas_values = []
    humidity_values = []

    for i in range(samples):
        temp_c, humidity, pressure, gas = read_sensor()

        print("Sample", i + 1, "/", samples)
        print("Humidity:", humidity, "Gas:", gas)
        
        oled_message("CALIBRATING", "Sample {}/{}".format(i + 1, samples), "Hum:{:.1f}%".format(humidity), "")

        if gas is not None and gas > 0:
            gas_values.append(gas)

        if humidity is not None and humidity > 0:
            humidity_values.append(humidity)

        time.sleep(1)

    baseline_gas = sum(gas_values) / len(gas_values)
    baseline_humidity = sum(humidity_values) / len(humidity_values)

    print("-------------------------")
    print("Calibration complete.")
    print("Baseline gas:", baseline_gas)
    print("Baseline humidity:", baseline_humidity)
    print("-------------------------")
    
    oled_message("Calibration", "complete!", "Monitoring...", "")
    
    time.sleep(1)

    return baseline_gas, baseline_humidity


def choose_state(gas_change, humidity_change, current_state, recovery_started):
    """
    Decide the next system state.

    Returns:
        next_state
        updated recovery timer
    """

    # Strong change: immediately enter or remain in ALERT.
    if (
        gas_change >= GAS_ALERT_THRESHOLD
        or humidity_change >= HUMIDITY_ALERT_THRESHOLD
    ):
        return "ALERT", None

    # Moderate change: enter or remain in SPIKE_DETECTED.
    if (
        gas_change >= GAS_WARNING_THRESHOLD
        or humidity_change >= HUMIDITY_WARNING_THRESHOLD
    ):
        return "SPIKE_DETECTED", None

    # If the system was previously in ALERT or SPIKE_DETECTED,
    # require a stable recovery period before returning to NORMAL.
    if current_state in ("ALERT", "SPIKE_DETECTED", "RECOVERY"):

        readings_stable = (
            gas_change < GAS_RECOVERY_THRESHOLD
            and humidity_change < HUMIDITY_RECOVERY_THRESHOLD
        )

        if readings_stable:
            if recovery_started is None:
                recovery_started = time.ticks_ms()

            recovery_elapsed = time.ticks_diff(
                time.ticks_ms(),
                recovery_started
            )

            if recovery_elapsed >= RECOVERY_TIME_MS:
                return "NORMAL", None

            return "RECOVERY", recovery_started

        # The air has not stabilized enough.
        return "SPIKE_DETECTED", None

    return "NORMAL", None

#------------------------------
# Button function
#------------------------------
def recalibration_requested():
    """Return True after the button is held for about one second."""
    if recalibrate_button.value() == 0:
        press_started = time.ticks_ms()

        while recalibrate_button.value() == 0:
            if time.ticks_diff(
                time.ticks_ms(),
                press_started
            ) >= 1000:
                return True

            time.sleep_ms(20)

    return False

# -----------------------------
# Main program
# -----------------------------

all_leds_off()
buzzer_off()
oled_clear()

print("Starting Air Quality Event Monitor")

print("Sensor devices:", ["0x{:02X}".format(device) for device in i2c_sensor.scan()])


oled_message(
    "Air Monitor",
    "Starting...",
    "Pico 2",
    ""
)

time.sleep (2)

baseline_gas, baseline_humidity = calibrate(samples=15)

print("Starting live monitoring...")

# =========================================================
# Main Monitoring Group
# =========================================================

previous_state = None
current_state = "NORMAL"
recovery_started = None

last_alert_beep = time.ticks_ms()

try:
    while True:
        if recalibration_requested():
            print("Manual recalibration requested.")
            all_leds_off()
            buzzer_off()
            oled_message(
                "RECALIBRATING",
                "Keep air still",
                "Please wait...",
                "")
            baseline_gas, baseline_humidity = calibrate(
                samples = CALIBRATION_SAMPLES)
            
            current_state = "NORMAL"
            previous_state = None
            recovery_started = None
            last_alert_beep = time.ticks_ms()
            
            print("Manual recalibration complete.")
            # Prevent the same button press from triggering again
            
            while recalibrate_button.value() == 0:
                time.sleep_ms(20)
    
            time.sleep_ms(200)
            
        
        #-------------------------------------------------------------
        # Recovery sensor safely
        #-------------------------------------------------------------
        try:
            temp_c, humidity, pressure, gas = read_sensor()
            
        except OSError as error:
            current_state = "ERROR"
            show_state(current_state)
            show_error_on_oled("Sensor failure")
            
            print ("Sensor communication error:", error)
            
            time.sleep(1)
            continue
        #-------------------------------------------------------------
        # Calculate changes from baseline
        #-------------------------------------------------------------

        gas_change = percent_change(
            gas,
            baseline_gas
        )

        humidity_change = percent_change(
            humidity,
            baseline_humidity
        )
        
        #-------------------------------------------------------------
        # State machine decision
        #-------------------------------------------------------------

        current_state, recovery_started = choose_state(
        gas_change,
        humidity_change,
        current_state,
        recovery_started)
        

        # Update LEDs and buzzer only when the state changes.
        if current_state != previous_state:
            show_state(current_state)
            
            print("State changed:", previous_state, "->", current_state)
            
            #Beep imedately whe Alert first begins
            if current_state == "ALERT":
                alert_beep()
                last_alert_beep = time.ticks_ms()
                
            else:
                buzzer_off()
                
            previous_state = current_state
        
        #Continue beeping periodically during ALERT
        if current_state == "ALERT":
            now = time.ticks_ms()
            
            if time.ticks_diff(now, last_alert_beep) >= ALERT_BEEP_INTERVALS_MS:
                
                alert_beep()
                last_alert_beep = now

        # Update the OLED every sensor reading.
        try:
            update_oled(current_state, temp_c, humidity, gas_change, humidity_change)
            
        except OSError as error:
            print("OLED communication error:", error)
        
        

        temp_f = (temp_c * 9 / 5) + 32

        print("-------------------------")
        print("State:", current_state)
        print(
            "Temperature: {:.2f} C / {:.2f} F".format(
                temp_c,
                temp_f
            )
        )
        print("Humidity: {:.2f}%".format(humidity))
        print("Pressure: {:.2f} hPa".format(pressure))
        print("Gas:", gas)
        print("Gas change: {:.2f}%".format(gas_change))
        print(
            "Humidity change: {:.2f}%".format(
                humidity_change
            )
        )

        delay_started = time.ticks_ms()
        
        while time.ticks_diff(
            time.ticks_ms(),
            delay_started) < SAMPLE_INTERVAL_MS:
            time.sleep_ms(50)
            

        
#Clean UP

except KeyboardInterrupt:
    
    print ("Stop requested.")
    
finally:
    all_leds_off()
    buzzer_off()
    
    try: 
        oled_clear()
        
    except OSError:
        pass
    
    print("Harbware outputs cleared.") 
    