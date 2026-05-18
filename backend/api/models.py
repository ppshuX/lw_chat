from django.conf import settings
from django.db import models


class ChatGroup(models.Model):
    name = models.CharField(max_length=80)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_groups")
    announcement = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    ROLE_OWNER = "owner"
    ROLE_MEMBER = "member"
    ROLE_CHOICES = (
        (ROLE_OWNER, "群主"),
        (ROLE_MEMBER, "成员"),
    )

    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "user")
        ordering = ["-role", "joined_at"]

    def __str__(self):
        return f"{self.group.name} - {self.user.username}"


class PrivateMessage(models.Model):
    TYPE_TEXT = "text"
    TYPE_IMAGE = "image"
    TYPE_CHOICES = (
        (TYPE_TEXT, "文本"),
        (TYPE_IMAGE, "图片"),
    )

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_private_messages")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_private_messages")
    content = models.TextField(blank=True, default="")
    message_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_TEXT)
    image_url = models.URLField(max_length=500, blank=True, default="")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender_id}->{self.receiver_id}: {self.message_type}"


class GroupMessage(models.Model):
    TYPE_TEXT = "text"
    TYPE_IMAGE = "image"
    TYPE_CHOICES = (
        (TYPE_TEXT, "文本"),
        (TYPE_IMAGE, "图片"),
    )

    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_group_messages")
    content = models.TextField(blank=True, default="")
    message_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_TEXT)
    image_url = models.URLField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.group_id}:{self.sender_id}: {self.message_type}"
