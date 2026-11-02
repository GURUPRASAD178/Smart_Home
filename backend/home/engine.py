"""Automation rules. Pure Django, no hardware knowledge: feed it readings,
ask it which outputs should be on."""

from django.utils import timezone

from .models import Config, Device, Event, Reading

DEVICES = ("light", "fan", "buzzer")
HYSTERESIS = 1.0  # fan switches off this many degrees below the threshold
KEEP_READINGS = 2000


def set_device(name, on, message):
    """Change a device and log it, but only when the state really changes."""
    device = Device.get(name)
    if device.is_on != on:
        device.is_on = on
        device.save(update_fields=["is_on"])
        Event.log(message)


def process(temp, motion, now=None):
    now = now or timezone.now()
    cfg = Config.get()
    temp = round(float(temp), 1)

    Reading.objects.create(temp=temp, motion=bool(motion))
    old = Reading.objects.order_by("-id").values_list("id", flat=True)[KEEP_READINGS:]
    if old:
        Reading.objects.filter(id__in=list(old)).delete()

    if motion:
        cfg.last_motion_at = now

    if cfg.armed and motion and not cfg.alarm_active:
        cfg.alarm_active = True
        Event.log("Motion detected while the alarm is armed", Event.ALERT)
    cfg.save()

    # Light: on while there was motion within the last `light_timeout` seconds.
    if Device.get("light").auto:
        recent = (
            cfg.last_motion_at is not None
            and (now - cfg.last_motion_at).total_seconds() <= cfg.light_timeout
        )
        if recent:
            set_device("light", True, "Light turned on: motion detected")
        else:
            set_device(
                "light", False, f"Light turned off: no motion for {cfg.light_timeout} s"
            )

    # Fan: on above the threshold, off once it has cooled by HYSTERESIS.
    if Device.get("fan").auto:
        fan_on = Device.get("fan").is_on
        if temp >= cfg.temp_threshold:
            set_device("fan", True, f"Fan turned on: {temp}°C is above {cfg.temp_threshold:g}°C")
        elif fan_on and temp <= cfg.temp_threshold - HYSTERESIS:
            set_device("fan", False, f"Fan turned off: cooled to {temp}°C")

    # Buzzer: follows the alarm.
    if Device.get("buzzer").auto:
        if cfg.alarm_active:
            set_device("buzzer", True, "Buzzer started: alarm triggered")
        else:
            set_device("buzzer", False, "Buzzer stopped")


def device_states():
    return {name: Device.get(name).is_on for name in DEVICES}


def set_armed(armed):
    cfg = Config.get()
    if cfg.armed == armed:
        return cfg
    cfg.armed = armed
    if not armed:
        cfg.alarm_active = False
    cfg.save()
    Event.log("Alarm armed" if armed else "Alarm disarmed")
    return cfg


def silence_alarm():
    cfg = Config.get()
    if cfg.alarm_active:
        cfg.alarm_active = False
        cfg.save()
        Event.log("Alarm silenced")
    return cfg


def manual_device(name, on):
    device = Device.get(name)
    device.auto = False
    device.is_on = on
    device.save()
    Event.log(f"{name.capitalize()} turned {'on' if on else 'off'} by hand")


def auto_device(name):
    device = Device.get(name)
    if not device.auto:
        device.auto = True
        device.save(update_fields=["auto"])
        Event.log(f"{name.capitalize()} back on automatic")
