# Nombre del Proyecto

ProyectoFSEm-Invernadero

Este proyecto tiene la el proposito de proporcionar un control automatizado para un invernadero utilizando las tarjetas de desarrollo Raspberry Pi y Arduino UNO

GitHub: https://github.com/SodaasINC/ProyectoFSEm-Invernadero

## Tabla de Contenidos

1. [Instalación](#instalación)
2. [Uso](#uso)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Contribución](#contribución)
5. [Licencia](#licencia)
6. [Version](#version)

## Instalación

Para poder ejecutar este proyecto instale en su Raspberry Pi el sistema operativo Raspberry Pi OS Desktop y ejecute el archivo de configuración config.sh

Para el módulo de Arduino descargue Arduino IDE, conecte su tarjeta, seleccione el puerto y envíe el código *.ccp

## Uso

El sistema esta desarrollado para funcionar principalmente de forma automática, por lo que la unica interacción que el usuario puede realizar es, mediante la interfáz provista por la Raspberry Pi, y mediante el uso de un mouse, controlar el deslizador para modular lo potencia del ventilador usando PWM.

## Estructura del Proyecto

Este proyecto se compone por:
doc/ incluye la documentación del proyecto
src/ contiene el archivo invernadero.py y arduino.cpp
vid/ contiene un archivo de texto con el link a la videodemostración del funcionamiento del proyecto

## Licencia

MIT License

## Versión

0.0.1