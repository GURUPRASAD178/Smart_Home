from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from . import engine
from .models import Config, Device, Event


class RuleTests(TestCase):
    def test_fan_turns_on_above_threshold_and_off_with_hysteresis(self):
        engine.process(27.0, False)
        self.assertFalse(Device.get("fan").is_on)
        engine.process(28.5, False)
        self.assertTrue(Device.get("fan").is_on)
        engine.process(27.5, False)  # still within the 1 degree band
        self.assertTrue(Device.get("fan").is_on)
        engine.process(26.9, False)
        self.assertFalse(Device.get("fan").is_on)

    def test_light_follows_motion_then_times_out(self):
        now = timezone.now()
        engine.process(25, True, now)
        self.assertTrue(Device.get("light").is_on)
        engine.process(25, False, now + timedelta(seconds=5))
        self.assertTrue(Device.get("light").is_on)
        engine.process(25, False, now + timedelta(seconds=11))
        self.assertFalse(Device.get("light").is_on)

    def test_armed_alarm_triggers_buzzer_until_silenced(self):
        engine.set_armed(True)
        engine.process(25, True)
        self.assertTrue(Config.get().alarm_active)
        self.assertTrue(Device.get("buzzer").is_on)
        self.assertTrue(Event.objects.filter(kind="alert").exists())
        engine.silence_alarm()
        engine.process(25, False)
        self.assertFalse(Device.get("buzzer").is_on)

    def test_unarmed_motion_does_not_sound_alarm(self):
        engine.process(25, True)
        self.assertFalse(Config.get().alarm_active)

    def test_manual_override_beats_automation_until_auto_is_restored(self):
        engine.manual_device("fan", False)
        engine.process(35, False)
        self.assertFalse(Device.get("fan").is_on)
        engine.auto_device("fan")
        engine.process(35, False)
        self.assertTrue(Device.get("fan").is_on)


class ApiTests(TestCase):
    def test_status_shape(self):
        engine.process(26.4, False)
        data = self.client.get("/api/status/").json()
        self.assertEqual(data["reading"]["temp"], 26.4)
        self.assertEqual(set(data["devices"]), {"light", "fan", "buzzer"})

    def test_device_toggle_and_validation(self):
        r = self.client.post("/api/devices/fan/", {"on": True}, content_type="application/json")
        self.assertEqual(r.json(), {"name": "fan", "on": True, "auto": False})
        self.assertEqual(self.client.post("/api/devices/toaster/", {}, content_type="application/json").status_code, 404)
        self.assertEqual(self.client.post("/api/devices/fan/", {"on": "yes"}, content_type="application/json").status_code, 400)

    def test_config_rejects_silly_values(self):
        r = self.client.post("/api/config/", {"temp_threshold": 500}, content_type="application/json")
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/api/config/", {"temp_threshold": 30}, content_type="application/json")
        self.assertEqual(r.json()["temp_threshold"], 30.0)
