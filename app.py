from flask import Flask, render_template, jsonify
import serial
import threading
import time

app = Flask(__name__)

# Inicializácia sériového portu – uprav podľa svojho portu
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

# Zoznam na uchovávanie údajov
light_data = []

# Funkcia na čítanie údajov zo sériového portu
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
                    # ponecháme len posledných 100 hodnôt
                    if len(light_data) > 100:
                        light_data = light_data[-100:]
                except:
                    pass

# Spustenie čítacieho vlákna
threading.Thread(target=read_from_serial, daemon=True).start()

# Hlavná stránka – zobrazuje základné HTML
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint na získanie údajov vo formáte JSON
@app.route('/light_data')
def get_light_data():
    return jsonify(light_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
