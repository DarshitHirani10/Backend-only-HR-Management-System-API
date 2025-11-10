from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification

"""
This file is not needed. Use Notification.objects.create and rely on signals for real-time delivery.
"""
