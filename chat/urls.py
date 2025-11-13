from django.urls import path
from chat.views import CreatePrivateRoomView, CreateGroupRoomView,ListRoomsView, RoomMessagesView, SendMessageAPIView

urlpatterns = [
    path("rooms/private/", CreatePrivateRoomView.as_view(), name="create-private-room"),
    path("rooms/group/", CreateGroupRoomView.as_view(), name="create-group-room"),
    path("rooms/", ListRoomsView.as_view(), name="list-rooms"),
    path("rooms/<int:room_id>/messages/", RoomMessagesView.as_view(), name="room-messages"),
    path("rooms/<int:room_id>/messages/send/", SendMessageAPIView.as_view(), name="send-message"),
]
