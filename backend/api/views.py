from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view

from .models import ChatGroup, GroupMember, GroupMessage, PrivateMessage
from .serializers import (
    group_member_payload,
    group_message_payload,
    group_payload,
    private_message_payload,
    user_payload,
)


def ok(data=None, message="ok", status=200):
    payload = {"code": status, "message": message}
    if data is not None:
        payload["data"] = data
    return JsonResponse(payload, status=status)


def fail(message, status=400):
    return JsonResponse({"code": status, "message": message}, status=status)


def request_user_id(request):
    raw = request.headers.get("X-User-Id") or request.GET.get("user_id")
    if not raw and hasattr(request, "data"):
        raw = request.data.get("user_id")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def get_request_user(request):
    user_id = request_user_id(request)
    if not user_id:
        return None
    return User.objects.filter(id=user_id).first()


@csrf_exempt
@api_view(["POST"])
def register_view(request):
    username = (request.data.get("username") or "").strip()
    password = request.data.get("password") or ""
    nickname = (request.data.get("nickname") or username).strip()
    if not username or not password:
        return fail("请输入用户名和密码")
    if User.objects.filter(username=username).exists():
        return fail("用户名已存在")

    user = User.objects.create_user(username=username, password=password, first_name=nickname)
    return ok({"user": user_payload(user)}, "注册成功")


@csrf_exempt
@api_view(["POST"])
def login_view(request):
    username = (request.data.get("username") or "").strip()
    password = request.data.get("password") or ""
    user = authenticate(username=username, password=password)
    if not user:
        return fail("用户名或密码错误", 401)
    return ok({"user": user_payload(user)}, "登录成功")


@api_view(["GET"])
def users_view(request):
    current_user_id = request_user_id(request)
    users = User.objects.filter(is_active=True).order_by("id")
    if current_user_id:
        users = users.exclude(id=current_user_id)
    return ok([user_payload(user) for user in users])


@api_view(["GET"])
def conversations_view(request):
    user = get_request_user(request)
    if not user:
        return fail("缺少用户身份", 401)

    users = User.objects.filter(is_active=True).exclude(id=user.id).order_by("id")
    private_items = []
    for peer in users:
        last_message = (
            PrivateMessage.objects.filter(Q(sender=user, receiver=peer) | Q(sender=peer, receiver=user))
            .select_related("sender", "receiver")
            .order_by("-created_at")
            .first()
        )
        unread = PrivateMessage.objects.filter(sender=peer, receiver=user, is_read=False).count()
        private_items.append(
            {
                "type": "private",
                "id": f"private-{peer.id}",
                "target_id": peer.id,
                "name": user_payload(peer)["nickname"],
                "avatar_text": user_payload(peer)["avatar_text"],
                "last_message": format_last_message(last_message),
                "last_time": last_message.created_at.strftime("%H:%M") if last_message else "",
                "unread": unread,
                "peer": user_payload(peer),
            }
        )

    groups = ChatGroup.objects.select_related("owner").prefetch_related("memberships__user").order_by("-created_at")
    group_items = []
    for group in groups:
        membership = GroupMember.objects.filter(group=group, user=user).first()
        last_message = group.messages.select_related("sender").order_by("-created_at").first()
        group_items.append(
            {
                "type": "group",
                "id": f"group-{group.id}",
                "target_id": group.id,
                "name": group.name,
                "avatar_text": group.name[:1].upper(),
                "last_message": format_last_message(last_message),
                "last_time": last_message.created_at.strftime("%H:%M") if last_message else "",
                "unread": 0,
                "joined": bool(membership),
                "group": group_payload(group, user.id),
            }
        )

    return ok({"private": private_items, "groups": group_items})


def format_last_message(message):
    if not message:
        return "暂无消息"
    if message.message_type == "image":
        return "[图片]"
    return message.content[:36] or "空消息"


@api_view(["GET"])
def private_messages_view(request):
    user = get_request_user(request)
    peer_id = request.GET.get("peer_id")
    if not user or not peer_id:
        return fail("缺少用户或会话参数")
    peer = User.objects.filter(id=peer_id).first()
    if not peer:
        return fail("用户不存在", 404)

    messages = (
        PrivateMessage.objects.filter(Q(sender=user, receiver=peer) | Q(sender=peer, receiver=user))
        .select_related("sender", "receiver")
        .order_by("created_at")
    )
    PrivateMessage.objects.filter(sender=peer, receiver=user, is_read=False).update(is_read=True)
    return ok([private_message_payload(message) for message in messages])


@csrf_exempt
@api_view(["GET", "POST"])
def groups_view(request):
    user = get_request_user(request)
    if request.method == "GET":
        groups = ChatGroup.objects.select_related("owner").prefetch_related("memberships__user").order_by("-created_at")
        return ok([group_payload(group, user.id if user else None) for group in groups])

    if not user:
        return fail("缺少用户身份", 401)
    name = (request.data.get("name") or "").strip()
    if not name:
        return fail("请输入群聊名称")
    group = ChatGroup.objects.create(name=name, owner=user, announcement="欢迎加入群聊。")
    GroupMember.objects.create(group=group, user=user, role=GroupMember.ROLE_OWNER)
    return ok(group_payload(group, user.id), "群聊创建成功")


@csrf_exempt
@api_view(["POST"])
def join_group_view(request, group_id):
    user = get_request_user(request)
    if not user:
        return fail("缺少用户身份", 401)
    group = ChatGroup.objects.filter(id=group_id).first()
    if not group:
        return fail("群聊不存在", 404)
    GroupMember.objects.get_or_create(group=group, user=user, defaults={"role": GroupMember.ROLE_MEMBER})
    return ok(group_payload(group, user.id), "已加入群聊")


@api_view(["GET"])
def group_members_view(request, group_id):
    members = GroupMember.objects.filter(group_id=group_id).select_related("user", "group")
    return ok([group_member_payload(member) for member in members])


@api_view(["GET"])
def group_messages_view(request):
    group_id = request.GET.get("group_id")
    if not group_id:
        return fail("缺少群聊参数")
    messages = GroupMessage.objects.filter(group_id=group_id).select_related("sender").order_by("created_at")
    return ok([group_message_payload(message) for message in messages])


@csrf_exempt
@api_view(["PUT"])
def group_announcement_view(request, group_id):
    user = get_request_user(request)
    group = ChatGroup.objects.filter(id=group_id).first()
    if not user or not group:
        return fail("群聊不存在或缺少用户身份", 404)
    if group.owner_id != user.id:
        return fail("只有群主可以修改公告", 403)
    group.announcement = (request.data.get("announcement") or "").strip()
    group.save(update_fields=["announcement"])
    return ok(group_payload(group, user.id), "公告已更新")


@csrf_exempt
@api_view(["DELETE"])
def remove_group_member_view(request, group_id, member_id):
    user = get_request_user(request)
    group = ChatGroup.objects.filter(id=group_id).first()
    if not user or not group:
        return fail("群聊不存在或缺少用户身份", 404)
    if group.owner_id != user.id:
        return fail("只有群主可以移除成员", 403)
    member = GroupMember.objects.filter(id=member_id, group=group).first()
    if not member:
        return fail("该成员不存在", 404)
    if member.user_id == group.owner_id:
        return fail("不能移除群主")
    member.delete()
    return ok(message="该成员已移除")


@csrf_exempt
@api_view(["POST"])
def upload_image_view(request):
    image = request.FILES.get("file")
    if not image:
        return fail("请选择图片")
    if not image.content_type.startswith("image/"):
        return fail("只能上传图片文件")
    storage = FileSystemStorage(location=settings.MEDIA_ROOT / "chat_images", base_url="/media/chat_images/")
    filename = storage.save(image.name, image)
    return ok({"url": storage.url(filename)}, "上传成功")
