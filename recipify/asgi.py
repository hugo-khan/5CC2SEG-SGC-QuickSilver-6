"""
ASGI config for recipify project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

# Called on import and safe to call repeatedly even if module cached
if os.environ.get("DJANGO_SETTINGS_MODULE") != "recipify.settings":
    os.environ["DJANGO_SETTINGS_MODULE"] = "recipify.settings"

application = get_asgi_application()
