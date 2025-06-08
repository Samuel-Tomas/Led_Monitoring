from flask import Flask, render_template, request, jsonify
import serial
import threading
import time

app = Flask(__name__)

# Inicializácia sériového portu
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

# Globálne premenné
light_data = []
system_open = False
monitoring_active = False
current_brightness = 0

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
                except:
                    pass

# Spustenie vlákna na čítanie
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
        return jsonify({'sensor': 0, 'voltage': 0.0, 'brightness': 0})
    if light_data:
        last = light_data[-1][1]
        voltage = round((last * 5.0) / 1023, 2)
    else:
        last = 0
        voltage = 0.0
    return jsonify({'sensor': last, 'voltage': voltage, 'brightness': current_brightness})

@app.route('/set_brightness', methods=['POST'])
def set_brightness():
    global current_brightness
    percent = int(request.form['percent'])
    brightness = int(percent * 2.55)
    current_brightness = percent
    if system_open:
        ser.write(f"{brightness}\n".encode())
    return '', 204

@app.route('/toggle_open', methods=['POST'])
def toggle_open():
    global system_open, light_data
    system_open = not system_open
    if system_open:
        print("🔓 Systém otvorený")
        light_data = []
        ser.write(b"INIT\n")
        ser.write(b"2\n")
    else:
        print("🔒 Systém zatvorený")
        ser.write(b"0\n")
    return jsonify({'system_open': system_open})

@app.route('/toggle_monitoring', methods=['POST'])
def toggle_monitoring():
    global monitoring_active
    monitoring_active = not monitoring_active
    print("📊 Monitorovanie:", "Aktívne" if monitoring_active else "Zastavené")
    return jsonify({'monitoring_active': monitoring_active})

@app.route('/status')
def get_status():
    return jsonify({'system_open': system_open, 'monitoring_active': monitoring_active})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


