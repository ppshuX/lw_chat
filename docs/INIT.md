# LwChat 技术文档

**项目地址：** [https://github.com/ppshuX/lw_chat](https://github.com/ppshuX/lw_chat)

## 1. 项目概述

LwChat 是一个课程作业级 Web 聊天交互系统。系统采用前后端分离结构，前端负责聊天界面和交互，后端负责用户、消息、群聊、图片上传和 WebSocket 实时通信。

项目目标是实现一个可以本地运行、可演示、可截图、方便写报告的轻量聊天系统。

## 2. 项目背景

即时聊天系统是 Web 应用中常见的交互场景，涉及用户认证、数据持久化、前后端接口、实时通信和文件上传等内容。通过实现 LwChat，可以较完整地理解一个聊天系统从页面交互到后端存储、再到 WebSocket 推送的基本流程。

本项目参考微信网页版和 QQ 聊天界面的基本布局，保留课程作业所需的核心功能，避免引入 Redis、Docker、云服务等复杂依赖。

## 3. 项目目标

- 实现用户注册、登录和退出。
- 实现用户列表和会话列表。
- 实现一对一私聊，支持文本和图片消息。
- 实现群聊创建、加入、群消息发送和成员查看。
- 实现群公告修改和群主角色展示。
- 使用 WebSocket 实现实时消息收发。
- 使用 SQLite 保存历史消息，支持刷新后加载。
- 提供简洁、耐看的三栏聊天界面。

## 4. 技术选型

### 前端

```txt
Vue3 + Vite + TypeScript + CSS
```

选择原因：

- Vue3 适合快速构建组件化交互界面。
- Vite 启动和构建速度快，适合课程项目演示。
- TypeScript 提升前端数据结构的清晰度。
- 自定义 CSS 便于精细控制聊天界面样式。

### 后端

```txt
Django + Django REST Framework + Django Channels
```

选择原因：

- Django 提供成熟的用户系统和 ORM。
- Django REST Framework 适合编写 HTTP API。
- Django Channels 支持 WebSocket，能实现实时聊天。
- 项目结构清晰，适合文档和报告说明。

### 数据库

```txt
SQLite
```

选择原因：

- 无需单独安装数据库服务。
- 适合本地开发和课程演示。
- 能满足用户、消息、群聊等数据持久化需求。

## 5. 系统架构

```txt
Vue3 前端
  -> HTTP API：注册、登录、会话、历史消息、群管理、图片上传
  -> WebSocket：私聊消息、群聊消息

Django 后端
  -> DRF 视图函数：处理普通 HTTP 请求
  -> Channels Consumer：处理 WebSocket 连接和消息广播

SQLite
  -> 保存用户、私聊消息、群聊、群成员、群消息

media/chat_images
  -> 保存聊天图片文件
```

## 6. 功能模块设计

### 用户模块

用户模块基于 Django 自带 `User` 模型实现。系统使用 `username` 作为登录账号，使用 `first_name` 保存演示昵称。前端登录后将用户信息保存到 `localStorage` 的 `lwchat_user` 中，用于刷新后保持登录状态。

主要功能：

- 注册用户
- 登录用户
- 退出登录
- 获取用户列表

### 私聊模块

私聊模块用于两个用户之间发送消息。前端点击左侧用户会话后，先通过 HTTP 加载历史记录，再通过 WebSocket 实时接收新消息。

主要功能：

- 加载私聊历史消息
- 发送文本消息
- 发送图片消息
- 自己消息靠右，对方消息靠左
- 消息保存到 SQLite

### 群聊模块

群聊模块支持创建群聊、加入群聊和发送群消息。群聊消息通过群房间 WebSocket 广播给当前连接的用户。

主要功能：

- 创建群聊
- 加入群聊
- 加载群聊历史消息
- 发送群消息
- 查看群成员

### 群管理模块

群管理采用简化实现。创建群聊的用户为群主，群主可以修改群公告并移除普通成员。

主要功能：

- 群主标识
- 修改群公告
- 查看成员列表
- 移除普通成员

### 图片消息模块

图片消息先通过 HTTP 上传到后端，后端保存文件并返回 URL。前端再通过 WebSocket 发送一条 `message_type=image` 的消息。

主要功能：

- 选择图片
- 上传图片
- 保存到 `media/chat_images/`
- 聊天窗口展示图片

### 离线消息模块

系统没有实现复杂推送。离线消息通过数据库持久化体现：所有消息都会保存到 SQLite，用户重新登录或刷新后，通过历史消息接口加载。

## 7. 数据库设计

### User

Django 内置用户表，主要使用字段：

```txt
id          用户 ID
username    用户名
password    加密密码
first_name  昵称
```

### PrivateMessage

```txt
id            消息 ID
sender        发送者
receiver      接收者
content       文本内容或图片地址
message_type  text / image
image_url     图片地址
is_read       是否已读
created_at    创建时间
```

### ChatGroup

```txt
id            群聊 ID
name          群名称
owner         群主
announcement  群公告
created_at    创建时间
```

### GroupMember

```txt
id          记录 ID
group       群聊
user        用户
role        owner / member
joined_at   加入时间
```

### GroupMessage

```txt
id            消息 ID
group         群聊
sender        发送者
content       文本内容或图片地址
message_type  text / image
image_url     图片地址
created_at    创建时间
```

## 8. 接口设计

### 用户接口

```txt
POST /api/register/
POST /api/login/
GET  /api/users/
```

### 会话接口

```txt
GET /api/conversations/?user_id=<id>
```

### 私聊接口

```txt
GET /api/private-messages/?user_id=<id>&peer_id=<id>
```

### 群聊接口

```txt
GET    /api/groups/
POST   /api/groups/
POST   /api/groups/<group_id>/join/
GET    /api/groups/<group_id>/members/
PUT    /api/groups/<group_id>/announcement/
DELETE /api/groups/<group_id>/members/<member_id>/
GET    /api/group-messages/?group_id=<id>
```

### 图片接口

```txt
POST /api/upload-image/
```

前端通过 `X-User-Id` 请求头传递当前演示用户身份。这是课程项目中的简化处理，不等同于生产环境认证方案。

## 9. WebSocket 设计

### 私聊 WebSocket

连接地址：

```txt
ws://localhost:8000/ws/private/<当前用户ID>/
```

发送文本消息：

```json
{
  "sender_id": 1,
  "receiver_id": 2,
  "message_type": "text",
  "content": "你好"
}
```

发送图片消息：

```json
{
  "sender_id": 1,
  "receiver_id": 2,
  "message_type": "image",
  "content": "/media/chat_images/a.png",
  "image_url": "/media/chat_images/a.png"
}
```

### 群聊 WebSocket

连接地址：

```txt
ws://localhost:8000/ws/group/<群聊ID>/
```

发送群消息：

```json
{
  "sender_id": 1,
  "group_id": 1,
  "message_type": "text",
  "content": "大家好"
}
```

Consumer 收到消息后，先保存到 SQLite，再通过 Channels group 广播给对应用户或群聊房间。

## 10. 前端页面设计

前端采用三栏布局：

- 左侧会话栏：当前用户、退出按钮、创建群聊、私聊列表、群聊列表。
- 中间聊天区：会话标题、消息列表、输入框、图片按钮、发送按钮。
- 右侧信息栏：私聊用户资料，或群公告、群成员和群主入口。

视觉风格以浅灰、白色、柔和绿色为主，避免复杂动画和夸张装饰，保证截图时清晰、克制、有产品感。

## 11. 本地运行方式

后端：

```bash
cd backend
python -m pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 8000
```

前端：

```bash
cd web
npm install
npm run dev
```

访问：

```txt
http://localhost:5173
```

## 12. 演示流程

1. 启动后端服务。
2. 启动前端服务。
3. 注册 `user1` 和 `user2`。
4. 普通浏览器登录 `user1`。
5. 无痕窗口登录 `user2`。
6. 演示私聊文本消息实时收发。
7. 演示私聊图片消息上传和展示。
8. 创建群聊，并让两个用户进入群聊。
9. 演示群聊消息发送。
10. 刷新页面后重新进入会话，展示历史消息。

## 13. 项目特点

- 本地运行简单，不依赖 Redis、Docker 或云服务。
- 功能闭环完整，覆盖注册、登录、私聊、群聊、图片、历史消息。
- 前后端分离，HTTP 和 WebSocket 分工清晰。
- 使用 SQLite 持久化消息，便于课程演示。
- UI 接近真实聊天软件，适合截图展示。

## 14. 后续扩展方向

- 好友申请和好友关系。
- 在线状态显示。
- 消息撤回。
- 表情消息。
- 群管理员角色。
- 未读消息持久化。
- 聊天记录搜索。
- 更完善的 Token 认证。

## 15. 项目总结

LwChat 实现了一个轻量聊天系统的核心功能。它通过 Django 提供 HTTP 和 WebSocket 服务，通过 SQLite 保存用户和消息数据，通过 Vue3 构建聊天界面。项目功能范围适合作业演示，结构清晰，启动成本低，可以较好地展示 Web 聊天系统的基本设计和实现过程。
