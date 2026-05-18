from django.contrib.auth.models import User

from .models import ChatGroup, GroupMember, GroupMessage, PrivateMessage


def user_payload(user):
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.first_name or user.username,
        "avatar_text": (user.first_name or user.username or "?")[:1].upper(),
    }


def private_message_payload(message):
    return {
        "id": message.id,
        "sender": user_payload(message.sender),
        "receiver": user_payload(message.receiver),
        "sender_id": message.sender_id,
        "receiver_id": message.receiver_id,
        "content": message.content,
        "message_type": message.message_type,
        "image_url": message.image_url,
        "created_at": message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "is_read": message.is_read,
    }


def group_payload(group, current_user_id=None):
    members = list(group.memberships.select_related("user"))
    current_role = ""
    for member in members:
        if current_user_id and member.user_id == current_user_id:
            current_role = member.role
            break
    return {
        "id": group.id,
        "name": group.name,
        "owner_id": group.owner_id,
        "owner": user_payload(group.owner),
        "announcement": group.announcement,
        "member_count": len(members),
        "current_role": current_role,
        "created_at": group.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def group_member_payload(member):
    return {
        "id": member.id,
        "role": member.role,
        "joined_at": member.joined_at.strftime("%Y-%m-%d %H:%M:%S"),
        "user": user_payload(member.user),
        "user_id": member.user_id,
    }


def group_message_payload(message):
    return {
        "id": message.id,
        "group_id": message.group_id,
        "sender": user_payload(message.sender),
        "sender_id": message.sender_id,
        "content": message.content,
        "message_type": message.message_type,
        "image_url": message.image_url,
        "created_at": message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
