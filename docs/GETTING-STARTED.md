# Smart home mini project

A small smart home you can run on your laptop today and wire to real hardware later.

- **Arduino Uno** reads temperature and an IR sensor, and drives a light, a fan and a buzzer.
- **Django** (backend) runs the rules and exposes a JSON API.
- **React** (frontend) shows a live dashboard and lets you control everything.

No Arduino yet? The backend has a built-in **simulator**, so the whole thing runs with zero hardware.

```
Arduino  <--USB serial-->  Django (rules + API + SQLite)  <--HTTP/JSON-->  React dashboard
                                  ^
                          or the simulator
```

## What it does

| Feature | Rule |
| --- | --- |
| Fan | Turns on at or above the temperature threshold (default 28 °C), off 1 °C below it |
| Light | Turns on when the IR sensor sees movement, off after 10 s without movement |
| Alarm | When armed, any movement sounds the buzzer until you silence or disarm it |
| Manual control | Flip any switch yourself. It stays manual until you press **Auto** |
| Activity log | Every change is recorded with a reason, e.g. "Fan turned on: 29.1°C is above 28°C" |

## Run it (simulator, no hardware)

You need Python 3.10+ and Node 18+.

**Terminal 1: backend**

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Terminal 2: frontend**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. In the **Simulator** panel, drag the temperature up past the threshold and press **Walk past the sensor** to watch the fan and light react.

Run the backend tests with `python manage.py test` (inside `backend`).

## Run it with the real Arduino

### 1. Parts

You already have everything needed: Uno, temperature sensor, IR sensor, buzzer, breadboard, wires.

The sketch uses the Uno's **built-in LED (D13) as the "light"**, so that costs nothing. For a visible "fan" on D10, pick one from your ₹200 budget (prices are rough):

| Option | Approx. cost | Notes |
| --- | --- | --- |
| LED + 220 Ω resistor | ₹5–15 | Simplest stand-in for a fan |
| 5 V relay module + small 5 V DC fan | ₹100–180 | Switches a real fan. Use a low-voltage DC fan only, not mains |

### 2. Wiring

| Part | Part pin | Uno pin |
| --- | --- | --- |
| LM35 or TMP36 | +Vs (left pin, flat side facing you) | 5V |
| | Vout (middle) | A0 |
| | GND (right) | GND |
| IR obstacle module | VCC / GND / OUT | 5V / GND / D2 |
| Active buzzer | + (long leg) / − | D8 / GND |
| Fan LED | long leg through 220 Ω | D10, short leg to GND |
| Fan relay (instead of LED) | IN / VCC / GND | D10 / 5V / GND |
| Light | built-in LED | D13 (nothing to wire) |

Use an **active** buzzer (it beeps when given power). If yours is passive, it needs `tone()` in the sketch instead.

### 3. Upload the sketch

1. Open `arduino/smart_home/smart_home.ino` in the Arduino IDE.
2. At the top, check the two options:
   - `TEMP_SENSOR_LM35` is `1` for LM35, `0` for TMP36.
   - `IR_ACTIVE_LOW` is `1` for most IR modules. If movement shows up inverted, set it to `0`.
3. Pick your board (Arduino Uno) and port, then upload.
4. Open the Serial Monitor at 9600 baud. You should see a line like `T:27.4,M:0` every second. Then **close the Serial Monitor**, because only one program can use the port.

Using a **DHT11** instead? Swap the body of `readTemperature()` for a DHT library call. Nothing else changes.

### 4. Point Django at the Arduino

```bash
pip install pyserial
```

Then start the backend with the serial port (find yours in the Arduino IDE's Tools > Port):

```bash
# macOS / Linux
HARDWARE=serial SERIAL_PORT=/dev/ttyACM0 python manage.py runserver

# Windows PowerShell
$env:HARDWARE="serial"; $env:SERIAL_PORT="COM3"; python manage.py runserver
```

The dashboard's status pill changes to "Live, Arduino connected", and the Simulator panel disappears.

If the Arduino stops responding, the pill turns red. If Django stops talking to the Arduino for 10 s, the Arduino switches all outputs off, so the buzzer can't get stuck on.

## How the Arduino and Django talk

Plain text lines over USB serial at 9600 baud.

- Arduino to Django, once per second: `T:27.4,M:0` (temperature, movement 0/1)
- Django to Arduino, every second: `SET,<light>,<fan>,<buzzer>` (each 0 or 1), e.g. `SET,1,0,0`

## API

All under `/api/`. Responses are JSON.

| Method and path | Body | Purpose |
| --- | --- | --- |
| `GET /status/` | | Latest reading, device states, settings, mode |
| `GET /readings/?limit=60` | | Recent temperature and movement history |
| `GET /events/?limit=12` | | Activity log, newest first |
| `POST /devices/<light\|fan\|buzzer>/` | `{"on": true}` or `{"auto": true}` | Switch by hand, or hand control back to the rules |
| `POST /config/` | `{"temp_threshold": 30, "light_timeout": 15}` | Change the rules |
| `POST /alarm/` | `{"armed": true}` or `{"silence": true}` | Arm, disarm or silence the alarm |
| `POST /sim/` | `{"temp": 31}` or `{"motion": true}` | Simulator only |

## Project layout

```
arduino/smart_home/smart_home.ino   Arduino sketch
backend/home/engine.py              the automation rules (start reading here)
backend/home/hardware.py            SimDriver and SerialDriver
backend/home/runner.py              background loop: read, apply rules, write outputs
backend/home/views.py, urls.py      the JSON API
backend/home/tests.py               tests for the rules and API
frontend/src/App.jsx                dashboard (polls the API every 1.5 s)
```

## Ideas for the next step

- **Cloud:** host Django somewhere free-tier, switch SQLite to Postgres, and add login.
- **Wireless:** replace the Uno and USB cable with an ESP8266 or ESP32 that posts readings over Wi-Fi (or MQTT), and add a `POST /api/readings/` endpoint for it. The rules in `engine.py` stay the same.
- **Alerts:** send a phone notification or email when the alarm triggers.
- **Live updates:** swap polling for WebSockets (Django Channels).
- **More rooms and sensors:** add a `room` field to readings and devices.
