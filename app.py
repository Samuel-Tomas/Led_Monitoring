from flask import Flask, render_template, request, jsonify
import serial
import threading
import time

app = Flask(__name__)
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

light_data = []

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

@app.route('/light_data')
def get_light_data():
    return jsonify(light_data)

@app.route('/set_brightness', methods=['POST'])
def set_brightness():
    percent = int(request.form['percent'])  # percento z formulára
    brightness = int(percent * 2.55)        # prevod na rozsah 0–255
    ser.write(f"{brightness}\n".encode())   # odoslanie do Arduina
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

