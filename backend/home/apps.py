import os
import sys

from django.apps import AppConfig


class HomeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "home"

    def ready(self):
        # Start the hardware loop only for the real dev server process
        # (not for migrate, tests, or the autoreloader's parent process).
        if "runserver" not in sys.argv:
            return
        if os.environ.get("RUN_MAIN") == "true" or "--noreload" in sys.argv:
            from . import runner

            runner.start()
