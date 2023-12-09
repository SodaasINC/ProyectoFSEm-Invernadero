/*
* arduino.cpp
*
* Authors:
*   Castro Serrato Luis Joaquin
*   Romero Trujillo Jerson Gerardo
*   Torres Martínez Marco Antonio
* Date:    2023.12.08
* License: MIT
*
*/

//Comunicación I2C
#include <Wire.h>

//Constantes
#define I2C_SLAVE_ADDR 0x0A
#define BOARD_LED 13
#define ZXPIN 2
#define TRIAC 3
#define ANALOG_PIN A0

//Variables globales
volatile bool flag = false;
float power = 0;
float mois = 0.0;
float pdelay = 0.0;
int inc = 1;

//Prototipos de función
void i2c_received_handler(int count);
void i2c_request_handler();

//Función de control de ángulo de disparo por detección de cruce por cero
void zxhandle() {
  flag = true;
  digitalWrite(TRIAC, LOW);
  digitalWrite(BOARD_LED, LOW);

  pdelay = -68.0 * power + 8000.0; // Calcular pdelay basado en power
  delayMicroseconds(static_cast<int>(pdelay));

  if (pdelay > 0.0) {
    digitalWrite(BOARD_LED, HIGH);
    digitalWrite(TRIAC, HIGH);
    delayMicroseconds(20);
    digitalWrite(TRIAC, LOW);
  }
}

// Configuración de las funciones de recepción y transmisión por I2C y de interrupción
void setup() {
  pinMode(ZXPIN, INPUT);
  attachInterrupt(0, zxhandle, RISING);
  pinMode(TRIAC, OUTPUT);
  pinMode(BOARD_LED, OUTPUT);
  
  Wire.begin(I2C_SLAVE_ADDR);
  Wire.onReceive(i2c_received_handler);
  Wire.onRequest(i2c_request_handler);
  
  Serial.begin(9600);
}

//Bucle principal
void loop() {
  char buffer[20];
  sprintf(buffer, "Power = %.2f\n", power);
  Serial.write(buffer);

  // Leer el valor analógico de A0 (sensor de humedad del suelo)
  int sensorValue = analogRead(ANALOG_PIN);
  mois = map(sensorValue, 0, 1023, 0, 100); // Mapear el valor a un rango de 0 a 100
  
  delay(1000);
}

// Repuesta I2C (Le el sensor de humedad analógico y envía el valor como porcentaje)
void i2c_request_handler() {
  int sensorValue = analogRead(A0); // Lee el valor del pin analógico A0
  float mappedValue = map(sensorValue, 0, 1023, 0, 100); // Mapea el valor de 0-1023 a 0-100
  
  float valueToSend = static_cast<float>(mappedValue); // Convierte a float
  
  // Enviar el valor mapeado como respuesta por I2C
  Wire.write((byte*)&valueToSend, sizeof(float));
}

//Recibe un dato de tipo flotante y lo almacena como potencia para su procesamiento
void i2c_received_handler(int count) {
  byte receivedData[sizeof(float)];
  if (count != sizeof(float)) return;
  
  for (byte i = 0; i < count; ++i)
    receivedData[i] = Wire.read();
  
  float receivedFloat;
  memcpy(&receivedFloat, receivedData, sizeof(receivedFloat));
  
  power = receivedFloat;
}