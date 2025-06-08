from flask import Flask, render_template, request, jsonify, send_from_directory
import serial
import threading
import time
import os
import csv
from datetime import datetime

app = Flask(__name__)

# Inicializácia sériového portu
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

# Globálne premenné
light_data = []
system_open = False
monitoring_active = False
brightness_percent = 0
current_filename = None

# Vytvorenie priečinka na históriu
os.makedirs("history", exist_ok=True)

# Čítanie údajov zo senzora
def read_from_serial():
    global light_data
    while True:
        if ser.in_waiting:
            line = ser.readline().decode().strip()
            if line.startswith("L:"):
                try:
                    raw = int(line[2:])
                    timestamp = int(time.time())
                    light_data.append((timestamp, raw))
                    if len(light_data) > 100:
                        light_data = light_data[-100:]

                    # Ukladanie do súboru, ak monitorujeme
                    if system_open and monitoring_active and current_filename:
                        with open(current_filename, "a", newline='') as f:
                            writer = csv.writer(f)
                            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            writer.writerow([now, raw, int(brightness_percent * 2.55), system_open, monitoring_active])
                except:
                    pass

threading.Thread(target=read_from_serial, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/values')
def values():
    return render_template('values.html')

@app.route('/gauges')
def gauges():
    return render_template('gauges.html')

@app.route('/history')
def history():
    files = sorted([f for f in os.listdir("history") if f.endswith(".csv")])
    selected = request.args.get("file")
    mode = request.args.get("mode", "table")

    data = []
    if selected:
        with open(f"history/{selected}", newline='') as f:
            reader = csv.reader(f)
            data = list(reader)[1:]

    return render_template("history.html", files=files, selected=selected, data=data, mode=mode)

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory("history", filename, as_attachment=True)

@app.route('/light_data')
def light_data_api():
    if not system_open or not monitoring_active:
        return jsonify([[int(time.time()), 0]])
    return jsonify(light_data)

@app.route('/latest_value')
def latest_value():
    if not system_open or not monitoring_active:
        return jsonify({'sensor': 0, 'voltage': 0.0})
    if light_data:
        last = light_data[-1][1]
        voltage = round((last * 5.0) / 1023, 2)
    else:
        last = 0
        voltage = 0.0
    return jsonify({'sensor': last, 'voltage': voltage})

@app.route('/set_brightness', methods=['POST'])
def set_brightness():
    global brightness_percent
    brightness_percent = int(request.form['percent'])
    brightness = int(brightness_percent * 2.55)
    if system_open:
        ser.write(f"{brightness}\n".encode())
    return '', 204

@app.route('/toggle_open', methods=['POST'])
def toggle_open():
    global system_open, light_data
    system_open = not system_open
    if system_open:
        light_data = []
        ser.write(b"INIT\n")
        ser.write(b"2\n")  # minimálna hodnota
    else:
        ser.write(b"0\n")
    return jsonify({'system_open': system_open})

@app.route('/toggle_monitoring', methods=['POST'])
def toggle_monitoring():
    global monitoring_active, current_filename
    monitoring_active = not monitoring_active

    if monitoring_active:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_filename = f"history/session_{now}.csv"
        with open(current_filename, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "sensor", "brightness", "open", "monitoring"])
    else:
        current_filename = None

    return jsonify({'monitoring_active': monitoring_active})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


