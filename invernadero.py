# -*- coding: utf-8 -*-
# ## #############################################################
#
# Author:
#   Castro Serrato Luis Joaquin
#   Romero Trujillo Jerson Gerardo
#   Torres Martínez Marco Antonio
# Date:    2023.12.08
# License: MIT 
#
# ## ############################################################
import RPi.GPIO as GPIO
import os
import sys
import smbus2
import struct
import time
import matplotlib.pyplot as plt
from datetime import datetime
import tkinter as tk
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Crear ventana principal
window = tk.Tk()
window.attributes('-fullscreen', True)
window.title("Control de Invernadero")

# Configura como pantalla completa
width=window.winfo_screenwidth()
height=window.winfo_screenheight()
window.geometry("%dx%d" % (width, height))
window.overrideredirect(True)

# Inicializar GPIO y pines PWM
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(24, GPIO.OUT, initial=GPIO.LOW) # Habilitación de la bomba de agua
pwm_pins = [32, 26] # Pines PWM para control de ventilador
arPWM = []
for pin in pwm_pins:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
    pwm = GPIO.PWM(pin, 10000)
    pwm.start(0) # Inicializa ciclo de trabajo en 100 (El ventilador se apaga en alto)
    arPWM.append(pwm)

# Arduino's I2C device address
SLAVE_ADDR = 0x0A

# Nombre de archivos de registro
LOG_FILE = './temp.log'
LGM_FILE = './mois.log'

#Temperatura esperada de día y noche
DESIRED_TEMPERATURE = 28.0
DESIRED_TEMPERATURE_NIGHT = 30.0
#Constantes PID
KP = 1
KI = 1
KD = 1
# Variables iniciales
prevError = 0 #e[k-1]
accError = 0 #Pi[k] = Kie[k] + Pi[k-1]
error = 0 #e[k]

i2c = smbus2.SMBus(1)

# Número máximo de puntos a plotear
MAX_DATA_POINTS = 10

#Función que retorna 'True' si son entre las 8:00 pm y las 6:00 am
def is_night():
    current_time = datetime.now().time()
    return current_time >= datetime.strptime('20:00:00', '%H:%M:%S').time() or current_time < datetime.strptime('06:00:00', '%H:%M:%S').time()

# Manejo de excepciones
def log_exception(ex):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print("EXCEPTION:", ex, fname, exc_tb.tb_lineno)

#Crea y escribe el histórico de temperatura
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

#Crea y escribe el histórico de humedad
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

#Genera las gráficas de humedad y temperatura
def plot_data():
    if not (os.path.exists(LOG_FILE) and os.path.exists(LGM_FILE)):
        return
    try:
        # Lectura del archivo de temperatura
        with open(LOG_FILE, 'r') as fp:
            lines = fp.readlines()
            time_data_temp = []
            temperature_data = []
            for line in lines:
                parts = line.split()
                if len(parts) == 2:
                    timestamp, temp = float(parts[0]), float(parts[1].replace('°C', ''))
                    time_data_temp.append(int(timestamp))
                    temperature_data.append(temp)

            # Limitar la cantidad de datos a mostrar
            if len(time_data_temp) > MAX_DATA_POINTS:
                time_data_temp = time_data_temp[-MAX_DATA_POINTS:]
                temperature_data = temperature_data[-MAX_DATA_POINTS:]

            # Crear la gráfica de temperatura
            fig_temp, ax_temp = plt.subplots()
            ax_temp.plot(time_data_temp, temperature_data, marker='o', color='red')
            ax_temp.set_title('Temperatura del invernadero')
            ax_temp.set_xlabel('Tiempo (s)')
            ax_temp.set_ylabel('Temperatura (°C)')
            ax_temp.set_ylim(10, 40)  # Limitar la escala vertical para temperatura

            plt.close('all')  # Cierra todas las figuras para liberar memoria

        # Lectura del archivo de humedad
        with open(LGM_FILE, 'r') as fp2:
            lines2 = fp2.readlines()
            time_data_hum = []
            moisture_data = []
            for line in lines2:
                parts = line.split()
                if len(parts) == 2:
                    timestamp, mois = float(parts[0]), float(parts[1])
                    time_data_hum.append(int(timestamp))
                    moisture_data.append(mois)

            # Limitar la cantidad de datos a mostrar
            if len(time_data_hum) > MAX_DATA_POINTS:
                time_data_hum = time_data_hum[-MAX_DATA_POINTS:]
                moisture_data = moisture_data[-MAX_DATA_POINTS:]

            # Crear la gráfica de humedad
            fig_hum, ax_hum = plt.subplots()
            ax_hum.plot(time_data_hum, moisture_data, marker='o')
            ax_hum.set_title('Humedad de la tierra')
            ax_hum.set_xlabel('Tiempo (s)')
            ax_hum.set_ylabel('Humedad (%)')
            ax_hum.set_ylim(0, 100)  # Limitar la escala vertical para humedad

            plt.close('all')  # Cierra todas las figuras para liberar memoria

            # Actualizar las gráficas en la interfaz gráfica
            act_graph(fig_temp, fig_hum)
    except Exception as e:
        print("Error al graficar:", e)

def act_graph(fig_temp, fig_hum):
    # Convierte las gráficas a imágenes compatibles con Tkinter
    canvas_temp = FigureCanvasTkAgg(fig_temp, master=window)
    canvas_temp.draw()
    imagen_pil_temp = Image.frombytes('RGB', canvas_temp.get_width_height(), canvas_temp.tostring_rgb())
    imagen_tk_temp = ImageTk.PhotoImage(imagen_pil_temp)

    canvas_mois = FigureCanvasTkAgg(fig_hum, master=window)
    canvas_mois.draw()
    imag_pil_mois = Image.frombytes('RGB', canvas_mois.get_width_height(), canvas_mois.tostring_rgb())
    imag_tk_mois = ImageTk.PhotoImage(imag_pil_mois)

    # Actualizar las etiquetas con las nuevas imágenes
    lab_imag_temp.config(image=imagen_tk_temp)
    lab_imag_temp.image = imagen_tk_temp

    lab_imag_mois.config(image=imag_tk_mois)
    lab_imag_mois.image = imag_tk_mois

#Lee temperatura via 1 Wire
def readTemperature():
    with open('/sys/bus/w1/devices/28-9a4a001d64ff/w1_slave', 'r') as file:
        lines = file.readlines()
        temperature_line = lines[1].strip()
        temperature_data = temperature_line.split('=')[-1]
        temperature = int(temperature_data)
        temperature /= 1000  # Convert to Celsius
        return temperature

#Envía al arduino la potencia para el detector ZC
def writePower(pwr):
	try:
		data = struct.pack('<f', pwr) # Packs number as float
		# Creates a message object to write 4 bytes from SLAVE_ADDR
		msg = smbus2.i2c_msg.write(SLAVE_ADDR, data)
		i2c.i2c_rdwr(msg)  # Performs write
	except:
		print("Envío fallido")
		pass

#Recibe la lectura analógica de la humedad como porcentaje
def readMois():
	try:
		# Creates a message object to read 4 bytes from SLAVE_ADDR
		msg = smbus2.i2c_msg.read(SLAVE_ADDR, 4)
		i2c.i2c_rdwr(msg)  # Performs write
		data = list(msg)   # Converts stream to list
		# list to array of bytes (required to decode)
		ba = bytearray()
		for c in data:
			ba.append(int(c))
		pwr = struct.unpack('<f', ba)
		# print('Received temp: {} = {}'.format(data, pwr))
		return pwr[0]
	except:
		print ("Error al leer")
		return None

# Manejo principal de los datos
def ctl():
    try:
        global accError
        global prevError
        cTemp = readTemperature()
        log_temp(cTemp) 
        print("\r Temperature: {:0.2f}°C".format(cTemp), end="")
        # Calcula el error en función del ciclo de día y noche
        if is_night():
            error = DESIRED_TEMPERATURE_NIGHT - cTemp
        else:
            error = DESIRED_TEMPERATURE - cTemp
        power = KP * error + KI * (error + accError) + KD * (error - prevError)
        writePower(power)
        # Actualiza parametros
        accError += error
        prevError = error
        
        cMois = 100 - readMois()
        print(" | Moisture: {}".format(cMois), end="")
        log_mois(cMois)  # Llama a la función log_mois() con la humedad actual

        if (cMois < 12 and is_night()):
            print("\nRegando")
            GPIO.output(24, GPIO.HIGH)
        else:
            GPIO.output(24, GPIO.LOW)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print("Exception in ctl: ", e)

# Modulación por ancho de pulso
def set_pwm():
    duty_cycle = slider.get()
    print(" | PWM = ", duty_cycle, end="")
    for i in range(len(arPWM)):
        arPWM[i].ChangeDutyCycle(100 - duty_cycle)

# Función para manejar el cambio en el deslizador
def act_sld(_):
    valor = slider.get()
    print("El valor del deslizador es:", valor)

# Función que se ejecuta cada segundo y que manda a llamar los controles principales
def inv():
    set_pwm()
    ctl()
    plot_data()
    window.after(1000, inv)

# Crear etiquetas para mostrar las imágenes de las gráficas
lab_imag_temp = tk.Label(window)
lab_imag_temp.pack()

lab_imag_mois = tk.Label(window)
lab_imag_mois.pack()

# Crear un deslizador (slider)
slider = tk.Scale(window, from_=0, to=100, orient=tk.HORIZONTAL, command=act_sld)
slider.pack()

# Crea texto
label = tk.Label(window, text="Potencia del ventilador")
label.pack

def main():
    try:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)

        if os.path.exists(LGM_FILE):
            os.remove(LGM_FILE)
            
        inv()
        
        def fullscr_out(event):
            window.attributes('-fullscreen', False)
        window.bind('<Escape>', fullscr_out)
        
        window.mainloop()

    except KeyboardInterrupt:
        pass
    except Exception as e:
        log_exception(e)
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()