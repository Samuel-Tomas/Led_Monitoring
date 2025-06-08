from flask import Flask, render_template, request, jsonify, send_from_directory
import serial
import threading
import time
import os
import csv
import sqlite3
from datetime import datetime

app = Flask(__name__)
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

# Globálne premenné
light_data = []
system_open = False
monitoring_active = False
brightness_percent = 0
current_csv = None

# Inicializuj databázu
os.makedirs("history", exist_ok=True)
conn = sqlite3.connect('history/data.db', check_same_thread=False)
cur = conn.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS measurements (
    timestamp TEXT,
    sensor INTEGER,
    brightness INTEGER
)''')
conn.commit()

# Čítanie údajov zo senzora
def read_from_serial():
    global light_data
    while True:
        if ser.in_waiting:
            line = ser.readline().decode().strip()
            if line.startswith("L:"):
                try:
                    raw = int(line[2:])
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    light_data.append((int(time.time()), raw))
                    if len(light_data) > 100:
                        light_data = light_data[-100:]

                    if monitoring_active:
                        # Zápis do CSV
                        if current_csv:
                            with open(f"history/{current_csv}", "a", newline="") as f:
                                writer = csv.writer(f)
                                writer.writerow([timestamp, raw, brightness_percent, system_open, monitoring_active])
                        # Zápis do DB
                        cur.execute("INSERT INTO measurements VALUES (?, ?, ?)", (timestamp, raw, brightness_percent))
                        conn.commit()
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
        ser.write(b"2\n")
    else:
        ser.write(b"0\n")
    return jsonify({'system_open': system_open})

@app.route('/toggle_monitoring', methods=['POST'])
def toggle_monitoring():
    global monitoring_active, current_csv
    monitoring_active = not monitoring_active
    if monitoring_active:
        filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + ".csv"
        current_csv = filename
        with open(f"history/{filename}", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "sensor", "brightness", "system_open", "monitoring"])
    else:
        current_csv = None
    return jsonify({'monitoring_active': monitoring_active})

@app.route('/history')
def history():
    files = os.listdir("history")
    files = [f for f in files if f.endswith('.csv')]
    selected = request.args.get('file')
    mode = request.args.get('mode', 'table')
    data = []
    if selected:
        with open(f"history/{selected}", newline="") as f:
            reader = csv.reader(f)
            next(reader)
            data = list(reader)
    return render_template('history.html', files=files, selected=selected, data=data, mode=mode)

@app.route('/dbhistory')
def db_history():
    mode = request.args.get('mode', 'table')
    selected = request.args.get('date')
    cur.execute("SELECT DISTINCT substr(timestamp, 1, 10) FROM measurements")
    dates = [r[0] for r in cur.fetchall()]
    data = []
    if selected:
        cur.execute("SELECT * FROM measurements WHERE timestamp LIKE ?", (selected + "%",))
        data = cur.fetchall()
    return render_template('dbhistory.html', dates=dates, selected=selected, data=data, mode=mode)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory("history", filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


