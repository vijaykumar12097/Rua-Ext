from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import RPi.GPIO as GPIO
import time
import threading

app = Flask(__name__)
CORS(app)

# ------------------------------
# GPIO Setup
# ------------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# ------------------------------
# Zones (UPDATED)
# ------------------------------
ZONE_PINS = {
    # Crowd Corridors
    "crowd_corridor_1": 5,
    "crowd_corridor_2": 6,
    "crowd_corridor_3": 13,
    "crowd_corridor_4": 16,
    "crowd_corridor_5": 19,

    # Roads & Areas
    "king_abdulaziz_road": 12,
    "haram_boulevard": 20,
    "al_amidah_road": 21,
    "prince_mohammed_bin_salman_road": 26,
    "salman_bin_abdulaziz_road": 17,
    "substation_and_utilities": 27,
    "masjid_al_haram": 22,
    "district_cooling_plant_1": 23,
}

# Initialize pins (OFF)
for pin in ZONE_PINS.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)

# ------------------------------
# Virtual Groups
# ------------------------------
VIRTUAL_ZONE_GROUPS = {

    # "crowd_corridors_all": [
    #     "crowd_corridor_1",
    #     "crowd_corridor_2",
    #     "crowd_corridor_3",
    #     "crowd_corridor_4",
    #     "crowd_corridor_5"
    # ],

    # "roadnames_surroundings": [
    #     "king_abdulaziz_road",
    #     "haram_boulevard",
    #     "al_amidah_road",
    #     "prince_mohammed_bin_salman_road",
    #     "salman_bin_abdulaziz_road",
    #     "substation_and_utilities",
    #     "masjid_al_haram",
    #     "district_cooling_plant_1"
    # ]
    
     "crowd_corridors_all": [
        "crowd_corridor_1",
        "crowd_corridor_2",
        "crowd_corridor_3",
        "crowd_corridor_4",
        "crowd_corridor_5"
    ],

    "main_roads": [
        "king_abdulaziz_road",
        "haram_boulevard",
        "al_amidah_road",
        "prince_mohammed_bin_salman_road",
        "salman_bin_abdulaziz_road"
    ],

    "roadnames_surroundings": [
        "main_roads",  # 👈 nested group
        "substation_and_utilities",
        "masjid_al_haram",
        "district_cooling_plant_1"
    ]
}

# ------------------------------
# Idle / Random Mode Config
# ------------------------------
last_activity_time = time.time()
IDLE_TIMEOUT = 120  # 2 minutes
RANDOM_MODE = False

# ------------------------------
# Helpers
# ------------------------------
# def resolve_zones(zones):
#     resolved = set()
#     for zone in zones:
#         if zone in VIRTUAL_ZONE_GROUPS:
#             resolved.update(VIRTUAL_ZONE_GROUPS[zone])
#         else:
#             resolved.add(zone)
#     return list(resolved)


def resolve_zones(zones):
    resolved = set()
    visited = set()

    def expand(zone):
        if zone in visited:
            return  # prevents infinite loops
        visited.add(zone)

        if zone in VIRTUAL_ZONE_GROUPS:
            for sub in VIRTUAL_ZONE_GROUPS[zone]:
                expand(sub)
        else:
            resolved.add(zone)

    for z in zones:
        expand(z)

    return list(resolved)


def set_zone(zone, state):
    zones = resolve_zones([zone])
    for z in zones:
        pin = ZONE_PINS.get(z)
        if pin is not None:
            GPIO.output(pin, GPIO.LOW if state else GPIO.HIGH)

def turn_off_all():
    for z in ZONE_PINS:
        set_zone(z, False)

# ------------------------------
# Random Mode Worker (Updated)
# ------------------------------
def random_mode_worker():
    global RANDOM_MODE

    while True:
        time.sleep(2)
        idle_time = time.time() - last_activity_time

        if idle_time > IDLE_TIMEOUT:
            RANDOM_MODE = True

        if RANDOM_MODE:
            print("[RANDOM MODE] Activating ALL zones")
            for zone in ZONE_PINS:
                set_zone(zone, True)
            time.sleep(10)  # small delay to prevent tight loop

# Start background thread
threading.Thread(target=random_mode_worker, daemon=True).start()

# ------------------------------
# Activity Tracker
# ------------------------------
def update_activity():
    global last_activity_time, RANDOM_MODE
    last_activity_time = time.time()
    RANDOM_MODE = False

# ------------------------------
# API Endpoints
# ------------------------------
@app.route('/status', methods=['GET'])
def get_status():
    update_activity()
    status = {
        zone: "ON" if GPIO.input(pin) == GPIO.LOW else "OFF"
        for zone, pin in ZONE_PINS.items()
    }
    return jsonify(status)

@app.route("/on_zone/<zone>", methods=["POST"])
def on_zone(zone):
    update_activity()
    zone = zone.lower()
    set_zone(zone, True)
    return jsonify({"status": "on", "zone": zone})

@app.route("/off_zone/<zone>", methods=["POST"])
def off_zone(zone):
    update_activity()
    zone = zone.lower()
    set_zone(zone, False)
    return jsonify({"status": "off", "zone": zone})

@app.route("/on_all", methods=["POST"])
def on_all():
    update_activity()
    for zone in ZONE_PINS:
        set_zone(zone, True)
    return jsonify({"status": "all on"})

@app.route("/off_all", methods=["POST"])
def off_all():
    update_activity()
    turn_off_all()
    return jsonify({"status": "all off"})

# ------------------------------
# UI Routes
# ------------------------------
@app.route('/')
def home():
    return render_template('index.html')

# ------------------------------
# Run App
# ------------------------------
if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)
    except KeyboardInterrupt:
        GPIO.cleanup()
    finally:
        GPIO.cleanup()