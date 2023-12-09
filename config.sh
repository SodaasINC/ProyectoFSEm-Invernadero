#!/bin/bash

# Bloquear la lectura de memorias USB
echo 'ACTION=="add", SUBSYSTEM=="usb", TEST=="authorized_default", ATTR{authorized_default}="0"' | sudo tee /etc/udev/rules.d/99-disable-usb-storage.rules
sudo udevadm control --reload-rules

# Eliminar el panel (barra de tareas)
mv ~/.config/lxpanel ~/.config/lxpanel_backup

# Bloquear las entradas del teclado (desactivación temporal)
sudo modprobe -r keyboard_module

# Instalar paquetes necesarios
sudo apt update
sudo apt install python3-smbus python3-matplotlib python3-pil -y

# Instalar set de herramientas de I2C
sudo apt-get install i2c-tools

# Habilitar la interfaz I2C
sudo raspi-config nonint do_i2c 0

# Agregar la línea dtoverlay=w1-gpio al final de /boot/config.txt
sudo sh -c 'echo "dtoverlay=w1-gpio" >> /boot/config.txt'

# Clona repositorio
git clone https://github.com/SodaasINC/ProyectoFSEm-Invernadero /home

# Agregar la ejecución del script Python al archivo rc.local
sudo sed -i -e '$i python3 /home/ProyectoFSEm-Invernadero/invernadero.py &\n' /etc/rc.local

# Reinicia el sistema
sudo reboot