import json

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from . import engine, runner
from .models import Config, Device, Event, Reading

# This API is meant for local use only, so POSTs skip CSRF (no cookies/login).


def _body(request):
    try:
        data = json.loads(request.body or b"{}")
        return data if isinstance(data, dict) else {}
    except ValueError:
        return {}


def _error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def _iso(dt):
    return timezone.localtime(dt).isoformat() if dt else None


def _limit(request, default, maximum):
    try:
        return max(1, min(int(request.GET.get("limit", default)), maximum))
    except ValueError:
        return default


def _config_json(cfg):
    return {
        "temp_threshold": cfg.temp_threshold,
        "light_timeout": cfg.light_timeout,
        "armed": cfg.armed,
        "alarm_active": cfg.alarm_active,
    }


@require_GET
def status(request):
    driver = runner.get_driver()
    latest = Reading.objects.order_by("-id").first()
    online = bool(latest and (timezone.now() - latest.created_at).total_seconds() < 6)
    return JsonResponse(
        {
            "mode": driver.mode if driver else "stopped",
            "online": online,
            "reading": latest
            and {"temp": latest.temp, "motion": latest.motion, "at": _iso(latest.created_at)},
            "devices": {
                name: {"on": d.is_on, "auto": d.auto}
                for name in engine.DEVICES
                for d in [Device.get(name)]
            },
            "config": _config_json(Config.get()),
        }
    )


@require_GET
def readings(request):
    limit = _limit(request, 60, 500)
    rows = list(Reading.objects.order_by("-id")[:limit])[::-1]
    return JsonResponse(
        {
            "readings": [
                {"temp": r.temp, "motion": r.motion, "at": _iso(r.created_at)} for r in rows
            ]
        }
    )


@require_GET
def events(request):
    rows = Event.objects.all()[: _limit(request, 15, 100)]
    return JsonResponse(
        {
            "events": [
                {"id": e.id, "kind": e.kind, "message": e.message, "at": _iso(e.created_at)}
                for e in rows
            ]
        }
    )


@csrf_exempt
@require_POST
def device(request, name):
    if name not in engine.DEVICES:
        return _error(f"Unknown device '{name}'. Use one of: {', '.join(engine.DEVICES)}.", 404)
    data = _body(request)
    if data.get("auto") is True:
        engine.auto_device(name)
    elif isinstance(data.get("on"), bool):
        engine.manual_device(name, data["on"])
    else:
        return _error('Send {"on": true|false} or {"auto": true}.')
    d = Device.get(name)
    return JsonResponse({"name": name, "on": d.is_on, "auto": d.auto})


@csrf_exempt
@require_POST
def config(request):
    data = _body(request)
    cfg = Config.get()
    if "temp_threshold" in data:
        try:
            value = float(data["temp_threshold"])
        except (TypeError, ValueError):
            return _error("temp_threshold must be a number.")
        if not 15 <= value <= 60:
            return _error("temp_threshold must be between 15 and 60 °C.")
        cfg.temp_threshold = round(value, 1)
    if "light_timeout" in data:
        try:
            seconds = int(data["light_timeout"])
        except (TypeError, ValueError):
            return _error("light_timeout must be a whole number of seconds.")
        if not 3 <= seconds <= 600:
            return _error("light_timeout must be between 3 and 600 seconds.")
        cfg.light_timeout = seconds
    cfg.save()
    return JsonResponse(_config_json(cfg))


@csrf_exempt
@require_POST
def alarm(request):
    data = _body(request)
    if isinstance(data.get("armed"), bool):
        cfg = engine.set_armed(data["armed"])
    elif data.get("silence") is True:
        cfg = engine.silence_alarm()
    else:
        return _error('Send {"armed": true|false} or {"silence": true}.')
    return JsonResponse(_config_json(cfg))


@csrf_exempt
@require_POST
def sim(request):
    driver = runner.get_driver()
    if driver is None or driver.mode != "sim":
        return _error("The simulator is only available when HARDWARE=sim.", 409)
    data = _body(request)
    if "temp" in data:
        try:
            driver.set_temp(float(data["temp"]))
        except (TypeError, ValueError):
            return _error("temp must be a number.")
    if data.get("motion") is True:
        driver.trigger_motion(3)
    return JsonResponse({"temp": round(driver.temp, 1)})
