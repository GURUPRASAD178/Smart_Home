"""Background loop: read the hardware, run the rules, update the outputs."""

import logging
import threading
import time

from django.conf import settings
from django.db import close_old_connections

from . import engine
from .hardware import SerialDriver, SimDriver

log = logging.getLogger(__name__)

_driver = None
_thread = None


def get_driver():
    return _driver


def _loop(driver):
    while True:
        started = time.time()
        close_old_connections()
        try:
            data = driver.read()
            if data:
                engine.process(data["temp"], data["motion"])
            driver.write(engine.device_states())
        except Exception:
            log.exception("Tick failed (did you run `python manage.py migrate`?)")
            time.sleep(2)
        if driver.mode == "sim":
            time.sleep(max(0.0, 1.0 - (time.time() - started)))


def start():
    global _driver, _thread
    if _thread and _thread.is_alive():
        return
    if settings.HARDWARE == "serial":
        _driver = SerialDriver(settings.SERIAL_PORT)
    else:
        _driver = SimDriver()
    log.info("Hardware mode: %s", _driver.mode)
    _thread = threading.Thread(target=_loop, args=(_driver,), daemon=True)
    _thread.start()
