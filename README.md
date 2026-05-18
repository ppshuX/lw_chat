# LwChat 聊天交互系统

LwChat 是一个课程作业级 Web 聊天交互系统，目标是本地可运行、可演示、可截图、结构清晰。系统参考轻量版微信/QQ 的聊天界面，实现注册登录、一对一私聊、群聊、图片消息、历史消息加载和基础群管理。

项目不追求商业级即时通信系统的完整复杂度，重点展示 Django 后端、Vue 前端、HTTP 接口、WebSocket 实时通信和 SQLite 持久化的完整流程。

## 技术栈

- 后端：Django、Django REST Framework、Django Channels
- 数据库：SQLite
- 实时通信：WebSocket，Channels 使用 `InMemoryChannelLayer`
- 前端：Vue3、Vite、TypeScript、TailwindCSS 依赖、自定义 CSS
- 文件存储：本地 `media/chat_images/`

## 功能特性

- 用户注册、登录、退出
- 页面刷新后通过 `localStorage` 保留当前演示用户
- 用户列表和会话列表展示
- 一对一私聊：文本消息、图片消息、历史消息、WebSocket 实时收发
- 群聊：创建群聊、加入群聊、发送群消息、查看群成员
- 群管理：群主标识、群公告修改、普通成员移除
- 图片上传：通过 HTTP 上传到后端，聊天窗口中展示图片消息
- 离线消息：所有消息保存到 SQLite，重新登录后可加载历史记录
- 三栏聊天 UI：左侧会话栏、中间聊天区、右侧信息栏

## 项目目录结构

```txt
LwChat/
├─ backend/
│  ├─ manage.py
│  ├─ requirements.txt
│  ├─ backend/
│  │  ├─ settings.py
│  │  ├─ urls.py
│  │  └─ asgi.py
│  └─ api/
│     ├─ models.py
│     ├─ views.py
│     ├─ urls.py
│     ├─ consumers.py
│     ├─ routing.py
│     ├─ serializers.py
│     └─ migrations/
├─ web/
│  ├─ package.json
│  ├─ vite.config.ts
│  └─ src/
│     ├─ App.vue
│     ├─ main.ts
│     └─ assets/
├─ docs/
│  ├─ INIT.md
│  ├─ REPORT.md
│  └─ DEMO.md
└─ README.md
```

## 后端启动步骤

```bash
cd backend
python -m pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 8000
```

后端默认地址：

```txt
http://localhost:8000
```

## 前端启动步骤

```bash
cd web
npm install
npm run dev
```

前端默认地址：

```txt
http://localhost:5173
```

前端默认连接：

```txt
HTTP API: http://localhost:8000
WebSocket: ws://localhost:8000
```

如需修改地址，可以在前端环境变量中设置 `VITE_API_BASE`。

## 测试账号创建方式

方式一：直接在前端注册页面创建 `user1` 和 `user2`。

方式二：使用 Django shell 创建：

```bash
cd backend
python manage.py shell
```

```python
from django.contrib.auth.models import User
User.objects.create_user(username="user1", password="123456", first_name="用户1")
User.objects.create_user(username="user2", password="123456", first_name="用户2")
```

## WebSocket 本地演示方法

1. 启动后端和前端。
2. 普通浏览器打开 `http://localhost:5173`，登录 `user1`。
3. 无痕窗口或另一个浏览器打开同一地址，登录 `user2`。
4. `user1` 点击左侧 `user2` 会话，发送文本消息。
5. `user2` 页面应实时收到消息。
6. `user2` 上传图片并发送，`user1` 页面应实时显示图片。
7. 创建群聊后，两个用户进入群聊并发送群消息。
8. 刷新页面后再次进入会话，历史消息仍可加载。

WebSocket 路径：

```txt
ws://localhost:8000/ws/private/<当前用户ID>/
ws://localhost:8000/ws/group/<群聊ID>/
```

## 图片上传说明

图片消息分两步完成：

1. 前端选择图片，通过 `POST /api/upload-image/` 上传。
2. 后端保存到 `backend/media/chat_images/`，返回图片 URL。
3. 前端通过 WebSocket 发送图片消息，聊天窗口按图片气泡展示。

开发环境下，Django 会通过 `/media/` 路由提供图片访问。

## 离线消息说明

LwChat 没有实现复杂的离线推送。系统采用简化实现：所有私聊消息和群聊消息都会保存到 SQLite。用户离线期间收到的消息不会丢失，重新登录或刷新页面后，前端通过历史消息接口重新加载。

## 项目截图说明

建议将截图放到：

```txt
docs/screenshots/
```

推荐截图内容：

- 登录或注册页面
- 私聊文本消息
- 私聊图片消息
- 群聊消息
- 右侧群公告和群成员列表
- 刷新后加载历史消息

## 常见问题

- 前端无法登录：确认后端已启动在 `http://localhost:8000`。
- WebSocket 不实时：确认使用 `python manage.py runserver 8000` 启动后端，浏览器控制台没有 WebSocket 连接错误。
- 图片不显示：确认图片已保存到 `backend/media/chat_images/`，并且返回地址以 `/media/chat_images/` 开头。
- 页面刷新后用户变化：点击“退出”会清理 `localStorage` 中的 `lwchat_user`。
- 多人群聊在多进程下不稳定：当前课程演示使用 `InMemoryChannelLayer`，适合本地单进程运行。

## 项目总结

LwChat 完成了一个轻量聊天系统的核心闭环：用户认证、会话选择、消息持久化、WebSocket 实时通信、图片上传和基础群聊管理。项目结构清晰，启动方式简单，适合作为课程作业进行演示、截图和报告说明。
