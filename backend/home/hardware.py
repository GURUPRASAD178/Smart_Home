"""Hardware drivers. Both expose the same two calls:

    read()   -> {"temp": float, "motion": bool} or None if nothing arrived
    write(s) -> push {"light": bool, "fan": bool, "buzzer": bool} to the outputs

SimDriver needs no hardware. SerialDriver talks to the Arduino sketch in
arduino/smart_home/smart_home.ino over USB.
"""

import logging
import random
import re
import time

log = logging.getLogger(__name__)


class SimDriver:
    mode = "sim"

    AMBIENT = 32.0  # the room warms towards this
    COOLED = 23.0  # the fan pulls the room towards this

    def __init__(self):
        self.temp = 26.0
        self.fan_on = False
        self.motion_until = 0.0

    def read(self):
        if self.fan_on:
            self.temp -= 0.08 * (self.temp - self.COOLED)
        else:
            self.temp += 0.03 * (self.AMBIENT - self.temp)
        self.temp += random.uniform(-0.05, 0.05)
        return {"temp": self.temp, "motion": time.time() < self.motion_until}

    def write(self, states):
        self.fan_on = states.get("fan", False)

    # Controls used by the dashboard's simulator panel.
    def set_temp(self, value):
        self.temp = float(value)

    def trigger_motion(self, seconds=3):
        self.motion_until = time.time() + seconds


class SerialDriver:
    mode = "serial"

    LINE = re.compile(r"T:(-?\d+(?:\.\d+)?),M:([01])")

    def __init__(self, port, baud=9600):
        self.port, self.baud = port, baud
        self.ser = None
        self._open()

    def _open(self):
        import serial  # pip install pyserial

        self.ser = serial.Serial(self.port, self.baud, timeout=1.5)
        time.sleep(2)  # the Uno resets when the port opens
        log.info("Opened Arduino on %s", self.port)

    def read(self):
        if self.ser is None:
            try:
                self._open()
            except Exception as exc:
                log.warning("Can't open %s: %s", self.port, exc)
                time.sleep(3)
                return None
        try:
            raw = self.ser.readline().decode(errors="ignore").strip()
        except Exception as exc:
            log.warning("Lost the Arduino: %s", exc)
            self.ser = None
            return None
        match = self.LINE.search(raw)
        if not match:
            return None
        return {"temp": float(match.group(1)), "motion": match.group(2) == "1"}

    def write(self, states):
        if self.ser is None:
            return
        line = "SET,{},{},{}\n".format(
            int(states.get("light", False)),
            int(states.get("fan", False)),
            int(states.get("buzzer", False)),
        )
        try:
            self.ser.write(line.encode())
        except Exception as exc:
            log.warning("Write failed: %s", exc)
            self.ser = None
