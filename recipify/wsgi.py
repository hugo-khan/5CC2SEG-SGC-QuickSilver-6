"""
WSGI config for recipify project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Always set DJANGO_SETTINGS_MODULE on import (tests may clear env)
if os.environ.get("DJANGO_SETTINGS_MODULE") != "recipify.settings":
    os.environ["DJANGO_SETTINGS_MODULE"] = "recipify.settings"

application = get_wsgi_application()
