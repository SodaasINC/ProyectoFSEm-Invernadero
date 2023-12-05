#include <Wire.h>

#define I2C_SLAVE_ADDR 0x0A
#define BOARD_LED 13
#define ZXPIN 2
#define TRIAC 3
#define ANALOG_PIN A0

volatile bool flag = false;
float power = 0;
float mois = 0.0; // Variable para el dato del sensor de humedad del suelo
float pdelay = 0.0;
int inc = 1;

void i2c_received_handler(int count);
void i2c_request_handler();

void zxhandle() {
  flag = true;
  digitalWrite(TRIAC, LOW);
  digitalWrite(BOARD_LED, LOW);
  
  delayMicroseconds(static_cast<int>(pdelay));
  
  if (pdelay > 0.0) {
    digitalWrite(BOARD_LED, HIGH);
    digitalWrite(TRIAC, HIGH);
    delayMicroseconds(20);
    digitalWrite(TRIAC, LOW);
  }
}

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

void loop() {
  char buffer[20];
  sprintf(buffer, "Power = %.2f\n", power);
  Serial.write(buffer);

  // Leer el valor analógico de A0 (sensor de humedad del suelo)
  int sensorValue = analogRead(ANALOG_PIN);
  mois = map(sensorValue, 0, 1023, 0, 100); // Mapear el valor a un rango de 0 a 100
  
  delay(1000);
}

void i2c_request_handler() {
  pdelay = -68.0 * power + 8000.0; // Calcular pdelay basado en power
  
  // Enviar mois (dato de humedad) como respuesta por I2C
  Wire.write((byte*)&mois, sizeof(float));
}

void i2c_received_handler(int count) {
  byte receivedData[sizeof(float)];
  if (count != sizeof(float)) return;
  
  for (byte i = 0; i < count; ++i)
    receivedData[i] = Wire.read();
  
  float receivedFloat;
  memcpy(&receivedFloat, receivedData, sizeof(receivedFloat));
  
  power = receivedFloat;
}