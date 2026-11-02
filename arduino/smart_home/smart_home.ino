/*
  Smart home node for Arduino Uno

  Sends one line per second over USB serial:   T:27.4,M:0
    T = temperature in degrees C, M = 1 when the IR sensor sees something

  Listens for lines from the Django backend:   SET,<light>,<fan>,<buzzer>
    each value is 0 or 1, e.g.  SET,1,0,0

  Wiring (see README.md for the full table):
    LM35 / TMP36 signal -> A0          IR sensor OUT -> D2
    Active buzzer (+)   -> D8          Fan (LED or relay IN) -> D10
    "Light"             -> D13 (the Uno's built-in LED, no parts needed)
*/

#include <stdio.h>

// ---- Pins -------------------------------------------------------------
const uint8_t PIN_TEMP   = A0;
const uint8_t PIN_IR     = 2;
const uint8_t PIN_BUZZER = 8;
const uint8_t PIN_FAN    = 10;
const uint8_t PIN_LIGHT  = 13;

// ---- Options: change these to match your parts -----------------------------
#define TEMP_SENSOR_LM35 1    // 1 = LM35 (10 mV per degree), 0 = TMP36
#define IR_ACTIVE_LOW    1    // most IR obstacle modules pull OUT low when they see something

const unsigned long REPORT_MS  = 1000;    // how often to send a reading
const unsigned long FAILSAFE_MS = 10000;  // outputs go off if the backend goes quiet

unsigned long lastReport = 0;
unsigned long lastCommand = 0;
char lineBuf[32];
uint8_t lineLen = 0;

// Averages several samples to smooth out noise. If your sensor is a DHT11,
// replace the body of this function with a DHT library call.
float readTemperature() {
  long sum = 0;
  const uint8_t samples = 16;
  for (uint8_t i = 0; i < samples; i++) {
    sum += analogRead(PIN_TEMP);
    delay(2);
  }
  float raw = sum / (float)samples;
#if TEMP_SENSOR_LM35
  // Internal 1.1 V reference: 1023 counts = 1.1 V, LM35 gives 10 mV per degree.
  return raw * 1.1 / 1023.0 * 100.0;
#else
  // TMP36 on the default 5 V reference: 500 mV offset, 10 mV per degree.
  float volts = raw * 5.0 / 1023.0;
  return (volts - 0.5) * 100.0;
#endif
}

bool motionDetected() {
  bool level = digitalRead(PIN_IR) == HIGH;
#if IR_ACTIVE_LOW
  return !level;
#else
  return level;
#endif
}

void applyOutputs(int light, int fan, int buzzer) {
  digitalWrite(PIN_LIGHT,  light  ? HIGH : LOW);
  digitalWrite(PIN_FAN,    fan    ? HIGH : LOW);
  digitalWrite(PIN_BUZZER, buzzer ? HIGH : LOW);
}

void handleCommand(const char* text) {
  int light, fan, buzzer;
  if (sscanf(text, "SET,%d,%d,%d", &light, &fan, &buzzer) == 3) {
    applyOutputs(light, fan, buzzer);
    lastCommand = millis();
  }
}

void readSerial() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      lineBuf[lineLen] = '\0';
      lineLen = 0;
      handleCommand(lineBuf);
    } else if (c != '\r' && lineLen < sizeof(lineBuf) - 1) {
      lineBuf[lineLen++] = c;
    }
  }
}

void setup() {
  Serial.begin(9600);
  pinMode(PIN_IR, INPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_FAN, OUTPUT);
  pinMode(PIN_LIGHT, OUTPUT);
  applyOutputs(0, 0, 0);
#if TEMP_SENSOR_LM35
  analogReference(INTERNAL);   // 1.1 V reference gives finer resolution for LM35
  analogRead(PIN_TEMP);        // first reading after switching reference is unreliable
  delay(50);
#endif
}

void loop() {
  readSerial();

  unsigned long now = millis();

  if (now - lastReport >= REPORT_MS) {
    lastReport = now;
    Serial.print("T:");
    Serial.print(readTemperature(), 1);
    Serial.print(",M:");
    Serial.println(motionDetected() ? 1 : 0);
  }

  // If Django stops talking (crashed, cable pulled), don't leave the buzzer stuck on.
  if (now - lastCommand > FAILSAFE_MS) {
    applyOutputs(0, 0, 0);
  }
}
