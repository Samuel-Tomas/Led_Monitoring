from flask import Flask, render_template, request, jsonify
import serial
import threading
import time

app = Flask(__name__)

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

light_data = []
system_open = False
monitoring_active = False

def read_from_serial():
    global light_data
    while True:
        if ser.in_waiting:
            line = ser.readline().decode().strip()
            if line.startswith("L:"):
                try:
                    value = int(line[2:])
                    timestamp = int(time.time())
                    light_data.append((timestamp, value))
                    if len(light_data) > 100:
                        light_data = light_data[-100:]
                except:
                    pass

threading.Thread(target=read_from_serial, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_brightness', methods=['POST'])
def set_brightness():
    percent = int(request.form['percent'])
    brightness = int(percent * 2.55)
    if system_open:
        ser.write(f"{brightness}\n".encode())
    return '', 204

@app.route('/light_data')
def get_light_data():
    if not system_open or not monitoring_active:
        return jsonify([[int(time.time()), 0]])
    return jsonify(light_data)

@app.route('/toggle_open', methods=['POST'])
def toggle_open():
    global system_open, light_data
    system_open = not system_open
    if system_open:
        ser.write(b"INIT\n")
        ser.write(b"2\n")  # slabé biele svetlo
        light_data = []
        print("✅ Systém otvorený")
    else:
        ser.write(b"0\n")
        print("❌ Systém zatvorený")
    return jsonify({'system_open': system_open})

@app.route('/toggle_monitoring', methods=['POST'])
def toggle_monitoring():
    global monitoring_active
    monitoring_active = not monitoring_active
    print("🟡 Monitorovanie:", "Aktívne" if monitoring_active else "Zastavené")
    return jsonify({'monitoring_active': monitoring_active})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


