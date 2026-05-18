# LwChat 聊天交互系统

**项目地址：** [https://github.com/ppshuX/lw_chat](https://github.com/ppshuX/lw_chat)

LwChat 是一个课程作业级 Web 聊天交互系统，目标是本地可运行、可演示、可截图、结构清晰。系统参考轻量版微信/QQ 的聊天界面，实现注册登录、一对一私聊、群聊、图片消息、历史消息加载和基础群管理。

项目不追求商业级即时通信系统的完整复杂度，重点展示 Django 后端、Vue 前端、HTTP 接口、WebSocket 实时通信和 SQLite 持久化的完整流程。

## 技术栈

- 后端：Django、Django REST Framework、Django Channels（Daphne 开发服务器）
- 数据库：SQLite
- 实时通信：WebSocket；Channels 使用 `InMemoryChannelLayer`（适合本地单进程演示）
- 前端：Vue 3、Vite、TypeScript、自定义 CSS（单页 `App.vue`）
- 身份标识：HTTP 请求通过 `X-User-Id` 头传递当前用户（课程演示简化方案，非生产级 Token 认证）
- 文件存储：本地 `backend/media/chat_images/`

## 功能特性

- 用户注册、登录、退出
- 页面刷新后通过 `localStorage`（键名 `lwchat_user`）保留当前演示用户；点击「退出」会清除
- 左侧会话栏：「私聊」展示所有其他注册用户（兼作用户列表），「群聊」展示系统中全部群及最后一条消息预览
- 私聊未读角标：进入会话后标记已读
- 一对一私聊：文本、图片、历史消息；登录后保持私聊 WebSocket 连接；在**当前打开的私聊窗口**内实时显示消息，左侧会话列表同步更新未读角标
- 群聊：创建群聊、点击未加入的群自动加入、发送群消息、查看群成员
- 群管理：群主标识、群公告修改（仅群主）、移除普通成员（不可移除群主）
- 图片上传：HTTP 上传到后端，再通过 WebSocket 发送图片消息，聊天窗口以图片气泡展示
- 离线消息：所有消息写入 SQLite；刷新或重新登录后，进入对应会话时通过历史接口加载
- 三栏聊天 UI：左侧会话栏、中间聊天区、右侧信息栏（私聊资料 / 群公告与成员）

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
│     ├─ middleware.py
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

若提示端口被占用，可改用 `python manage.py runserver 8001`，并同步设置前端 `VITE_API_BASE`。

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

如需修改后端地址，在 `web` 目录创建 `.env` 并设置：

```txt
VITE_API_BASE=http://localhost:8000
```

## 测试账号创建方式

方式一：在前端注册页创建 `user1`、`user2` 等账号。

方式二：使用 Django shell：

```bash
cd backend
python manage.py shell
```

```python
from django.contrib.auth.models import User
User.objects.create_user(username="user1", password="123456", first_name="用户1")
User.objects.create_user(username="user2", password="123456", first_name="用户2")
```

## WebSocket 说明

| 类型 | 连接时机 | 路径 |
|------|----------|------|
| 私聊 | 登录成功后自动连接，直到退出 | `ws://localhost:8000/ws/private/<当前用户ID>/` |
| 群聊 | **仅当打开该群会话时**连接，切换会话会断开 | `ws://localhost:8000/ws/group/<群聊ID>/` |

未加入群聊的用户无法发送群消息；点击左侧未加入的群会自动调用加入接口。发送群消息前须已是群成员。

## WebSocket 本地演示方法

1. 启动后端和前端。
2. 普通浏览器打开 `http://localhost:5173`，登录 `user1`。
3. 无痕窗口或另一个浏览器打开同一地址，登录 `user2`。
4. `user1` 在左侧「私聊」点击 `user2` 并发送文本；`user2` 也需点击 `user1` 进入私聊窗口，此时应实时收到消息。
5. `user2` 上传图片并发送；`user1` 在**同一私聊会话**内应实时看到图片。
6. `user1` 创建群聊；`user2` 在左侧「群聊」点击该群（自动加入），**双方都停留在该群聊天窗口**，互发群消息应实时可见。
7. 刷新页面（仍保持登录）后，再次点击进入原会话，历史消息应完整加载。

## 图片上传说明

1. 前端选择图片，通过 `POST /api/upload-image/` 上传（登录状态下会自动附带 `X-User-Id`）。
2. 后端保存到 `backend/media/chat_images/`，返回以 `/media/chat_images/` 开头的 URL。
3. 前端通过当前会话的 WebSocket 发送 `message_type: image` 消息。
4. 开发环境下，Django 通过 `/media/` 提供图片访问。

## 离线消息说明

系统未实现推送服务。所有私聊、群聊消息均持久化到 SQLite。用户离线或关闭页面期间的消息不会丢失；刷新后凭 `localStorage` 恢复登录态，**进入对应会话**时调用历史消息接口加载记录。

## 项目截图说明

建议将截图放到 `docs/screenshots/`（需自行创建目录）。

推荐截图：登录/注册页、私聊文本与图片、群聊消息、右侧群公告与成员列表、刷新后的历史消息。

## 常见问题

- **前端无法登录**：确认后端已在 `http://localhost:8000`（或你配置的 `VITE_API_BASE`）运行。
- **私聊不实时**：确认浏览器控制台私聊 WebSocket 已连接；后端须用 `runserver` 启动（Daphne/ASGI）。
- **群聊不实时**：确认双方都在**该群的聊天窗口**内；在私聊界面时不会连接群 WebSocket。
- **图片不显示**：确认文件在 `backend/media/chat_images/`，返回 URL 以 `/media/chat_images/` 开头。
- **刷新后用户丢失**：仅「退出」会清除 `lwchat_user`；普通刷新应保留登录态。
- **端口 8000 被占用**：结束占用进程或换端口，并同步 `VITE_API_BASE`。
- **多进程/多实例群聊异常**：`InMemoryChannelLayer` 仅适合本地单进程演示。

## 项目总结

LwChat 完成了轻量聊天系统的核心闭环：用户认证、会话选择、消息持久化、WebSocket 实时通信、图片上传和基础群管理。文档与实现一致，适合作为课程作业进行本地演示、截图和报告说明。

源码仓库：[ppshuX/lw_chat](https://github.com/ppshuX/lw_chat)
