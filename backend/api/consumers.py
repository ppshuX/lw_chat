import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User

from .models import ChatGroup, GroupMember, GroupMessage, PrivateMessage
from .serializers import group_message_payload, private_message_payload


class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = int(self.scope["url_route"]["kwargs"]["user_id"])
        self.room_group_name = f"user_{self.user_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = await self.save_private_message(data)
        if not message:
            await self.send_json({"type": "error", "message": "消息发送失败"})
            return

        event = {"type": "private.message", "message": message}
        await self.channel_layer.group_send(f"user_{message['sender_id']}", event)
        if message["receiver_id"] != message["sender_id"]:
            await self.channel_layer.group_send(f"user_{message['receiver_id']}", event)

    async def private_message(self, event):
        await self.send_json({"type": "private_message", "message": event["message"]})

    async def send_json(self, payload):
        await self.send(text_data=json.dumps(payload, ensure_ascii=False))

    @database_sync_to_async
    def save_private_message(self, data):
        sender = User.objects.filter(id=data.get("sender_id")).first()
        receiver = User.objects.filter(id=data.get("receiver_id")).first()
        if not sender or not receiver:
            return None
        message_type = data.get("message_type") or PrivateMessage.TYPE_TEXT
        content = (data.get("content") or "").strip()
        image_url = data.get("image_url") or (content if message_type == PrivateMessage.TYPE_IMAGE else "")
        message = PrivateMessage.objects.create(
            sender=sender,
            receiver=receiver,
            content=content,
            message_type=message_type,
            image_url=image_url,
        )
        return private_message_payload(message)


class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = int(self.scope["url_route"]["kwargs"]["group_id"])
        self.room_group_name = f"group_{self.group_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = await self.save_group_message(data)
        if not message:
            await self.send_json({"type": "error", "message": "请先加入群聊"})
            return
        await self.channel_layer.group_send(self.room_group_name, {"type": "group.message", "message": message})

    async def group_message(self, event):
        await self.send_json({"type": "group_message", "message": event["message"]})

    async def send_json(self, payload):
        await self.send(text_data=json.dumps(payload, ensure_ascii=False))

    @database_sync_to_async
    def save_group_message(self, data):
        group = ChatGroup.objects.filter(id=self.group_id).first()
        sender = User.objects.filter(id=data.get("sender_id")).first()
        if not group or not sender:
            return None
        if not GroupMember.objects.filter(group=group, user=sender).exists():
            return None
        message_type = data.get("message_type") or GroupMessage.TYPE_TEXT
        content = (data.get("content") or "").strip()
        image_url = data.get("image_url") or (content if message_type == GroupMessage.TYPE_IMAGE else "")
        message = GroupMessage.objects.create(
            group=group,
            sender=sender,
            content=content,
            message_type=message_type,
            image_url=image_url,
        )
        return group_message_payload(message)
