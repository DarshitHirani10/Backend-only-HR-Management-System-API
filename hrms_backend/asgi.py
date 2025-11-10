"""
ASGI config for hrms_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

# Ensure settings are configured before importing modules that touch Django apps
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms_backend.settings')

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Instantiate the Django ASGI app to populate app registry before importing any modules
# that may import Django models (like notifications.consumers)
django_asgi_app = get_asgi_application()

# Import routing after the app registry is ready
from notifications import routing as notifications_routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            notifications_routing.websocket_urlpatterns
        )
    ),
})


