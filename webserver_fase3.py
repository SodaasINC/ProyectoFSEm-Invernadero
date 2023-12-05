from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import RPi.GPIO as GPIO
import os
import sys
import magic
import smbus2
import struct
import time
import matplotlib.pyplot as plt
import threading

# Manejo de excepciones
def log_exception(ex):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print("EXCEPTION:", ex, fname, exc_tb.tb_lineno)

# Inicializar GPIO y pines PWM
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(24, GPIO.OUT, initial=GPIO.LOW)
pwm_pins = [32, 26]
arPWM = []
for pin in pwm_pins:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
    pwm = GPIO.PWM(pin, 1000)
    pwm.start(100)  # Inicia el PWM con un duty cycle de 0
    arPWM.append(pwm)

# Arduino's I2C device address
SLAVE_ADDR = 0x0A  # I2C Address of Arduino 1

# Name of the file in which the log is kept
LOG_FILE = './temp.log'
LGM_FILE = './mois.log'

# Constants from PID controller
DESIRED_TEMPERATURE = 28.0
KP = 1
KI = 1
KD = 1

# Initialize the I2C bus;
# RPI version 1 requires smbus.SMBus(0)
i2c = smbus2.SMBus(1)

# Initialize lists to store temperature and time data
time_data = []
temperature_data = []

# Maximum number of data points to display on the plot
MAX_DATA_POINTS = 10

def log_temp(temperature):
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'a+') as fp:
                fp.write('{} {}°C\n'.format(time.time(), temperature))
        else:
            with open(LOG_FILE, 'w+') as fp:
                fp.write('{} {}°C\n'.format(time.time(), temperature))
    except Exception as e:
        log_exception(e)

def log_mois(mois):
    try:
        if os.path.exists(LGM_FILE):
            with open(LGM_FILE, 'a+') as fp:
                fp.write('{} {}\n'.format(time.time(), mois))
        else:
            with open(LGM_FILE, 'w+') as fp:
                fp.write('{} {}\n'.format(time.time(), mois))
    except Exception as e:
        log_exception(e)

def plot_data():
    time.sleep(1)
    while True:
        try:
            # Leer el archivo de registro y actualizar las listas
            with open(LOG_FILE, 'r') as fp:
                lines = fp.readlines()
                time_data = []
                temperature_data = []
                for line in lines:
                    parts = line.split()
                    if len(parts) == 2:
                        timestamp, temp = float(parts[0]), float(parts[1].replace('°C', ''))
                        time_data.append(int(timestamp))
                        temperature_data.append(temp)

            # Limitar la cantidad de datos a mostrar
            if len(time_data) > MAX_DATA_POINTS:
                time_data = time_data[-MAX_DATA_POINTS:]
                temperature_data = temperature_data[-MAX_DATA_POINTS:]

            # Crear la gráfica
            plt.plot(time_data, temperature_data, marker='o')
            plt.xlabel('Tiempo (segundos)')
            plt.ylabel('Temperatura (°C)')
            plt.ylim(10, 40)  # Limitar la escala vertical

            plt.savefig('./graph.png')  # Guarda la gráfica como 'graph.png'
            plt.clf()  # Limpia la gráfica para futuras actualizaciones

            time.sleep(1)
        except Exception as e:
            log_exception(e)
            
        try:
            # Leer el archivo de registro y actualizar las listas
            with open(LGM_FILE, 'r') as fp:
                lines = fp.readlines()
                time_data = []
                moisture_data = []
                for line in lines:
                    parts = line.split()
                    if len(parts) == 2:
                        timestamp, mois = float(parts[0]), float(parts[1])
                        time_data.append(int(timestamp))
                        moisture_data.append(mois)

            # Limitar la cantidad de datos a mostrar
            if len(time_data) > MAX_DATA_POINTS:
                time_data = time_data[-MAX_DATA_POINTS:]
                moisture_data = moisture_data[-MAX_DATA_POINTS:]

            # Crear la gráfica
            plt.plot(time_data, moisture_data, marker='o')
            plt.xlabel('Tiempo')
            plt.ylabel('Humedad')
            plt.ylim(0, 100)  # Limitar la escala vertical

            plt.savefig('./graphm.png')  # Guarda la gráfica como 'graphm.png'
            plt.clf()  # Limpia la gráfica para futuras actualizaciones

            time.sleep(1)
        except Exception as e:
            log_exception(e)

def readTemperature():
    with open('/sys/bus/w1/devices/28-b46b001d64ff/w1_slave', 'r') as file:
        lines = file.readlines()
        temperature_line = lines[1].strip()
        temperature_data = temperature_line.split('=')[-1]
        temperature = int(temperature_data)
        temperature /= 1000  # Convert to Celsius
        return temperature

def writePower(pwr):
	try:
		data = struct.pack('<f', pwr) # Packs number as float
		# Creates a message object to write 4 bytes from SLAVE_ADDR
		msg = smbus2.i2c_msg.write(SLAVE_ADDR, data)
		i2c.i2c_rdwr(msg)  # Performs write
	except:
		print("Envío fallido")
		pass

def readMois():
	try:
		msg = smbus2.i2c_msg.read(SLAVE_ADDR, 4)
		i2c.i2c_rdwr(msg)
		data = list(msg)
		ba = bytearray(data[0:4])
		mois = struct.unpack('<f', ba)
		#print('Received temp: {} = {}'.format(data, mois[0]))
		return mois[0]
	except:
		return None

def ctl():
    prevError = 0
    accError = 0

    while True:
        try:
            cTemp = readTemperature()
            log_temp(cTemp)  # Llama a la función log_temp() con la temperatura actual
            print("\r Temperature: {:0.2f}°C".format(cTemp), end="")
            # Calculate error: E(s) = R(s) - B(s)
            error = DESIRED_TEMPERATURE - cTemp
            # Calculate plant input: V(s) = KP × E(s)
            power = KP * error + KI * (error + accError) + KD * (error - prevError)
            writePower(power)
            # Update previous and accumulated error
            accError += error
            prevError = error
            
            cMois = readMois()
            log_mois(cMois)  # Llama a la función log_mois() con la humedad actual
            print(" | Moisture: {}".format(cMois), end="")

            if (cMois > 88):
                GPIO.output(24, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(24, GPIO.LOW)
        except KeyboardInterrupt:
            break
        except Exception as e:
            log_exception(e)

class WebServer(BaseHTTPRequestHandler):
    """Clase para manejar las solicitudes HTTP"""

    def _send_response(self, status_code, content_type):
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.end_headers()

    def do_GET(self):
        if self.path == '/':
            self._send_response(200, 'text/html')
            self._serve_ui_file()
        elif self.path == '/graph.png':
            self._serve_graph_image()
        else:
            self._serve_file(self.path[1:])

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length'))
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            self._parse_post(data)
        except Exception as e:
            log_exception(e)
            self.send_response(400)
            self.end_headers()

    def _serve_file(self, rel_path):
        if not os.path.isfile(rel_path):
            self.send_error(404)
            pass
            return
        self.send_response(200)
        mime = magic.Magic(mime=True)
        self.send_header("Content-type", mime.from_file(rel_path))
        self.end_headers()
        with open(rel_path, 'rb') as file:
            self.wfile.write(file.read())

    def _serve_ui_file(self):
        if not os.path.isfile("user_interface.html"):
            err = "user_interface.html not found."
            self.wfile.write(bytes(err, "utf-8"))
            print(err)
            return
        try:
            with open("user_interface.html", "rb") as f:
                content = f.read()
        except Exception as e:
            log_exception(e)
            content = "Error reading user_interface.html: " + str(e)
        self.wfile.write(content)

    def _serve_graph_image(self):
        try:
            with open('./graph.png', 'rb') as img_file:
                img_data = img_file.read()
            self.send_response(200)
            self.send_header("Content-type", "image/png")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            self.wfile.write(img_data)
        except Exception as e:
            log_exception(e)
            self.send_response(500)
            self.end_headers()

    def _parse_post(self, data):
        if 'action' in data and 'value' in data:
            action = data['action']
            value = data['value']
            if action == 'pwm':
                self._set_pwm(int(value))
                self.send_response(200)
                self.end_headers()
                return
        self.send_response(400)
        self.end_headers()

    def _set_pwm(self, duty_cycle):
        for i in range(len(arPWM)):
            arPWM[i].ChangeDutyCycle(100 - duty_cycle)

def main():
    try:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)

        if os.path.exists(LGM_FILE):
            os.remove(LGM_FILE)
        
        # Crear un hilo para la modulación de la temperatura
        ctl_thread = threading.Thread(target=ctl)
        ctl_thread.start()
        
        # Crear un hilo para la función de generación y guardado de la gráfica
        plt_thread = threading.Thread(target=plot_data)
        plt_thread.start()
        
        webServer = HTTPServer(('localhost', 8080), WebServer)
        print("Servidor iniciado en http://localhost:8080")
        webServer.serve_forever()

    except KeyboardInterrupt:
        pass
    except Exception as e:
        log_exception(e)
    finally:
        webServer.server_close()
        GPIO.cleanup()

if __name__ == "__main__":
    main()