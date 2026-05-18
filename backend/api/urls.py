from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.register_view),
    path("login/", views.login_view),
    path("users/", views.users_view),
    path("conversations/", views.conversations_view),
    path("private-messages/", views.private_messages_view),
    path("groups/", views.groups_view),
    path("groups/<int:group_id>/join/", views.join_group_view),
    path("groups/<int:group_id>/members/", views.group_members_view),
    path("groups/<int:group_id>/announcement/", views.group_announcement_view),
    path("groups/<int:group_id>/members/<int:member_id>/", views.remove_group_member_view),
    path("group-messages/", views.group_messages_view),
    path("upload-image/", views.upload_image_view),
]
