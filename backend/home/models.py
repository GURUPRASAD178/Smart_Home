from django.db import models


class Reading(models.Model):
    temp = models.FloatField()
    motion = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]


class Device(models.Model):
    """One row per output: light, fan, buzzer."""

    name = models.CharField(max_length=20, unique=True)
    is_on = models.BooleanField(default=False)
    auto = models.BooleanField(default=True)  # False = person is in control

    @classmethod
    def get(cls, name):
        obj, _ = cls.objects.get_or_create(name=name)
        return obj


class Event(models.Model):
    INFO = "info"
    ALERT = "alert"

    kind = models.CharField(max_length=10, default=INFO)
    message = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    @classmethod
    def log(cls, message, kind=INFO):
        return cls.objects.create(message=message, kind=kind)


class Config(models.Model):
    """Single row (pk=1) holding the settings and alarm state."""

    temp_threshold = models.FloatField(default=28.0)
    light_timeout = models.IntegerField(default=10)  # seconds without motion
    armed = models.BooleanField(default=False)
    alarm_active = models.BooleanField(default=False)
    last_motion_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
