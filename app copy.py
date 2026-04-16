from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_cors import CORS  # Enable CORS for cross-origin requests
import RPi.GPIO as GPIO

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# GPIO setup
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setwarnings(False)

# Zone-to-GPIO mapping
zone_pins = {
    "STUDIO": 17,           # GPIO17 - Pin 11
    "1 BEDROOM": 18,        # GPIO18 - Pin 12
    "2 BEDROOMS": 27,       # GPIO27 - Pin 13
    "3 BEDROOMS": 22,       # GPIO22 - Pin 15
    "ELEVATION LIGHTS": 23, # GPIO23 - Pin 16
    "DROPOFF AREA": 24,     # GPIO24 - Pin 18
    "SITE": 25,             # GPIO25 - Pin 22
    "AMENITIES": 12         # GPIO12 - Pin 32
}

# Initialize all pins as output and set them to LOW
for pin in zone_pins.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# Routes for frontend
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/al-marjan-world')
def al_marjan_world():
    return render_template('al-marjan-world.html')

@app.route('/fairmont-residences')
def fairmont_residences():
    return render_template('fairmont-residences.html')

@app.route("/location")
def location():
    return render_template("location.html")


@app.route("/location1")
def location1():
    return render_template("location1.html")

@app.route("/location2")
def location2():
    return render_template("location2.html")

@app.route("/gallery")
def image_gallery():
    return render_template("gallery.html")

@app.route("/video")
def video():
    return render_template("video.html")

# Routes for zone control
@app.route('/toggle', methods=['POST'])
def toggle_zone():
    """
    Toggle a specific zone ON/OFF.
    """
    data = request.get_json()
    zone = data.get('zone')

    if zone not in zone_pins:
        return jsonify({"error": "Invalid zone name"}), 400

    pin = zone_pins[zone]
    current_state = GPIO.input(pin)
    GPIO.output(pin, not current_state)  # Toggle state

    return jsonify({"zone": zone, "state": "ON" if not current_state else "OFF"})

@app.route('/status', methods=['GET'])
def get_status():
    """
    Get the status of all zones (ON/OFF).
    """
    status = {zone: "ON" if GPIO.input(pin) else "OFF" for zone, pin in zone_pins.items()}
    return jsonify(status)

@app.route('/off_all', methods=['POST'])
def turn_off_all():
    """
    Turn OFF all zones.
    """
    for pin in zone_pins.values():
        GPIO.output(pin, GPIO.HIGH)
    return jsonify({"status": "All zones turned OFF"})


@app.route('/on_all', methods=['POST'])
def turn_on_all():
    """
    Turn ON all zones.
    """
    for pin in zone_pins.values():
        GPIO.output(pin, GPIO.LOW)
    return jsonify({"status": "All zones turned ON"})

@app.route('/cleanup', methods=['POST'])
def cleanup():
    """
    Cleanup GPIO pins (optional endpoint).
    """
    GPIO.cleanup()
    return jsonify({"status": "GPIO cleaned up"})

@app.route('/runnung', methods=['POST'])
def runnung():
   
    return jsonify({"status": "runnung"})

# Run the Flask app
if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)
    except KeyboardInterrupt:
        cleanup()
        print("Application stopped by user.")
    finally:
        GPIO.cleanup()
