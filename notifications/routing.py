from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Accept optional leading slash to be resilient to different ASGI path formats
    re_path(r"^/?ws/notifications/$", consumers.NotificationConsumer.as_asgi()),
]
