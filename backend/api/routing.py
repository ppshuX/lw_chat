from django.urls import path

from .consumers import GroupChatConsumer, PrivateChatConsumer

websocket_urlpatterns = [
    path("ws/private/<int:user_id>/", PrivateChatConsumer.as_asgi()),
    path("ws/group/<int:group_id>/", GroupChatConsumer.as_asgi()),
]
