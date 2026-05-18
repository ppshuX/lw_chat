# **LwChat 聊天交互系统技术文档**

## 一、项目概述

### 1. 项目名称

**LwChat 聊天交互系统**

### 2. 项目背景

随着互联网通信方式的发展，即时聊天系统已经成为现代 Web 应用中非常常见的功能。为了理解用户注册、实时通信、消息存储、图片上传、群聊管理等基础功能的实现方式，本项目设计并实现了一个简化版 Web 聊天系统。

本系统参考微信、QQ 等常见聊天软件的基本交互形式，实现用户注册登录、私聊、群聊、图片消息、群管理、离线消息等功能，重点展示一个聊天系统从前端界面、后端接口、数据库存储到 WebSocket 实时通信的完整流程。

### 3. 项目目标

本项目的主要目标是实现一个可运行、可演示、可扩展的 Web 聊天系统。

系统需要完成以下目标：

1. 支持用户注册、登录和退出；
2. 支持用户之间进行一对一聊天；
3. 支持创建群聊和群聊消息发送；
4. 支持发送文本消息和图片消息；
5. 支持群主或管理员进行基础群管理；
6. 支持离线消息存储，用户重新登录后可以查看历史消息；
7. 设计简洁清晰的聊天界面，便于用户操作和课程演示。

---

## 二、技术选型

### 1. 前端技术

前端采用：

```txt
Vue3 + Vite + TailwindCSS
```

选择原因：

* Vue3 组件化开发方便，适合快速构建聊天页面；
* Vite 启动速度快，开发体验好；
* TailwindCSS 方便快速完成界面样式；
* 前端页面结构清晰，便于后续扩展。

### 2. 后端技术

后端采用：

```txt
Django + Django REST Framework + Django Channels
```

选择原因：

* Django 自带用户系统，适合快速实现注册登录；
* Django REST Framework 方便开发 HTTP 接口；
* Django Channels 支持 WebSocket，可实现实时聊天；
* 结构清晰，适合课程项目展示。

### 3. 数据库

数据库采用：

```txt
SQLite
```

选择原因：

* 无需额外安装数据库服务；
* 配置简单，适合作业和本地演示；
* 能够满足用户、消息、群聊等数据存储需求。

### 4. 通信方式

系统采用两种通信方式：

```txt
HTTP：用于注册、登录、用户列表、群聊管理、图片上传等普通请求。
WebSocket：用于聊天消息的实时发送和接收。
```

---

## 三、系统整体架构

系统整体分为四层：

```txt
前端页面层
   ↓
HTTP / WebSocket 通信层
   ↓
后端业务处理层
   ↓
数据库存储层
```

### 1. 前端页面层

前端主要负责：

* 登录注册页面展示；
* 聊天主界面展示；
* 用户列表展示；
* 群聊列表展示；
* 消息发送与接收；
* 图片选择和上传；
* 群成员和群公告展示。

### 2. 后端业务层

后端主要负责：

* 用户注册登录；
* 用户信息管理；
* 私聊消息处理；
* 群聊消息处理；
* 图片文件保存；
* 群成员管理；
* 离线消息存储；
* WebSocket 连接管理。

### 3. 数据库层

数据库主要保存：

* 用户信息；
* 私聊消息；
* 群聊信息；
* 群成员信息；
* 群聊消息；
* 图片消息路径；
* 消息已读状态。

---

## 四、功能模块设计

## 1. 用户模块

### 功能描述

用户模块用于完成用户注册、登录和身份识别。

### 主要功能

```txt
1. 用户注册
2. 用户登录
3. 用户退出
4. 获取当前用户信息
5. 获取用户列表
```

### 用户信息字段

```txt
id：用户ID
username：用户名
password：密码
nickname：昵称
avatar：头像
created_at：注册时间
```

---

## 2. 私聊模块

### 功能描述

私聊模块用于实现两个用户之间的一对一聊天。

### 主要功能

```txt
1. 选择用户进入聊天窗口
2. 发送文本消息
3. 发送图片消息
4. 实时接收消息
5. 加载历史消息
6. 显示未读消息数量
```

### 私聊流程

```txt
用户A选择用户B
   ↓
前端建立 WebSocket 连接
   ↓
用户A发送消息
   ↓
后端接收消息并保存数据库
   ↓
后端通过 WebSocket 推送给用户B
   ↓
用户B聊天窗口实时显示消息
```

---

## 3. 群聊模块

### 功能描述

群聊模块用于实现多个用户之间的共同聊天。

### 主要功能

```txt
1. 创建群聊
2. 加入群聊
3. 查看群成员
4. 发送群消息
5. 接收群消息
6. 查看群聊历史记录
```

### 群聊流程

```txt
用户创建群聊
   ↓
系统生成群聊记录
   ↓
用户加入群聊
   ↓
进入群聊 WebSocket 房间
   ↓
发送群消息
   ↓
后端保存消息并推送给群内成员
```

---

## 4. 群管理模块

### 功能描述

群管理模块用于实现群主或管理员对群聊的基础管理。

### 主要功能

```txt
1. 群主可以修改群公告
2. 群主可以查看群成员
3. 群主可以移除群成员
4. 群成员显示角色：群主 / 管理员 / 普通成员
```

### 角色设计

```txt
owner：群主
admin：管理员
member：普通成员
```

本项目主要实现群主权限，管理员功能可以作为扩展功能。

---

## 5. 图片消息模块

### 功能描述

图片消息模块用于支持用户在私聊或群聊中发送图片。

### 实现方式

```txt
1. 前端选择图片文件；
2. 通过 HTTP 接口上传图片；
3. 后端将图片保存到 media/chat_images/ 目录；
4. 后端返回图片 URL；
5. 前端通过 WebSocket 发送图片类型消息；
6. 聊天窗口根据 message_type 渲染图片。
```

### 消息类型设计

```txt
text：文本消息
image：图片消息
```

---

## 6. 离线消息模块

### 功能描述

离线消息模块用于保证用户不在线时也不会丢失消息。

### 实现方式

本系统中，所有聊天消息都会保存到数据库。
当用户离线时，消息仍然正常写入数据库。用户重新登录后，前端会调用历史消息接口，加载离线期间收到的消息。

### 离线消息逻辑

```txt
用户不在线
   ↓
其他用户发送消息
   ↓
后端保存消息到数据库
   ↓
用户重新登录
   ↓
前端请求历史消息
   ↓
显示离线期间收到的消息
```

这一方式实现简单稳定，适合课程项目展示。

---

# 五、数据库设计

## 1. 用户表 User

```txt
字段名          类型          说明
id              int           用户ID
username        varchar       用户名
password        varchar       密码
nickname        varchar       昵称
avatar          varchar       头像地址
created_at      datetime      注册时间
```

---

## 2. 私聊消息表 PrivateMessage

```txt
字段名          类型          说明
id              int           消息ID
sender_id       int           发送者ID
receiver_id     int           接收者ID
content         text          消息内容
message_type    varchar       消息类型：text / image
image_url       varchar       图片地址
is_read         boolean       是否已读
created_at      datetime      发送时间
```

---

## 3. 群聊表 ChatGroup

```txt
字段名          类型          说明
id              int           群聊ID
name            varchar       群聊名称
owner_id        int           群主ID
avatar          varchar       群头像
announcement    text          群公告
created_at      datetime      创建时间
```

---

## 4. 群成员表 GroupMember

```txt
字段名          类型          说明
id              int           记录ID
group_id        int           群聊ID
user_id         int           用户ID
role            varchar       群角色：owner / admin / member
joined_at       datetime      加入时间
```

---

## 5. 群聊消息表 GroupMessage

```txt
字段名          类型          说明
id              int           消息ID
group_id        int           群聊ID
sender_id       int           发送者ID
content         text          消息内容
message_type    varchar       消息类型：text / image
image_url       varchar       图片地址
created_at      datetime      发送时间
```

---

# 六、接口设计

## 1. 用户相关接口

### 用户注册

```txt
POST /api/register/
```

请求参数：

```json
{
  "username": "user1",
  "password": "123456",
  "nickname": "用户1"
}
```

返回结果：

```json
{
  "code": 200,
  "message": "注册成功"
}
```

---

### 用户登录

```txt
POST /api/login/
```

请求参数：

```json
{
  "username": "user1",
  "password": "123456"
}
```

返回结果：

```json
{
  "code": 200,
  "message": "登录成功",
  "user": {
    "id": 1,
    "username": "user1",
    "nickname": "用户1"
  }
}
```

---

### 获取用户列表

```txt
GET /api/users/
```

返回结果：

```json
{
  "code": 200,
  "data": [
    {
      "id": 1,
      "username": "user1",
      "nickname": "用户1"
    },
    {
      "id": 2,
      "username": "user2",
      "nickname": "用户2"
    }
  ]
}
```

---

## 2. 私聊相关接口

### 获取私聊历史消息

```txt
GET /api/private-messages/?user_id=2
```

返回结果：

```json
{
  "code": 200,
  "data": [
    {
      "id": 1,
      "sender_id": 1,
      "receiver_id": 2,
      "content": "你好",
      "message_type": "text",
      "created_at": "2026-05-18 20:00:00"
    }
  ]
}
```

---

## 3. 群聊相关接口

### 创建群聊

```txt
POST /api/groups/
```

请求参数：

```json
{
  "name": "课程作业交流群"
}
```

返回结果：

```json
{
  "code": 200,
  "message": "群聊创建成功",
  "group_id": 1
}
```

---

### 获取群聊列表

```txt
GET /api/groups/
```

返回结果：

```json
{
  "code": 200,
  "data": [
    {
      "id": 1,
      "name": "课程作业交流群",
      "owner_id": 1
    }
  ]
}
```

---

### 获取群聊历史消息

```txt
GET /api/group-messages/?group_id=1
```

---

### 修改群公告

```txt
PUT /api/groups/1/announcement/
```

请求参数：

```json
{
  "announcement": "欢迎大家加入群聊，请文明交流。"
}
```

---

## 4. 图片上传接口

```txt
POST /api/upload-image/
```

请求参数：

```txt
file：图片文件
```

返回结果：

```json
{
  "code": 200,
  "url": "/media/chat_images/demo.png"
}
```

---

# 七、WebSocket 设计

## 1. 私聊 WebSocket 地址

```txt
ws://localhost:8000/ws/private/<user_id>/
```

示例：

```txt
ws://localhost:8000/ws/private/2/
```

### 私聊发送消息格式

```json
{
  "type": "private_message",
  "sender_id": 1,
  "receiver_id": 2,
  "message_type": "text",
  "content": "你好"
}
```

### 图片消息格式

```json
{
  "type": "private_message",
  "sender_id": 1,
  "receiver_id": 2,
  "message_type": "image",
  "content": "/media/chat_images/demo.png"
}
```

---

## 2. 群聊 WebSocket 地址

```txt
ws://localhost:8000/ws/group/<group_id>/
```

示例：

```txt
ws://localhost:8000/ws/group/1/
```

### 群聊发送消息格式

```json
{
  "type": "group_message",
  "group_id": 1,
  "sender_id": 1,
  "message_type": "text",
  "content": "大家好"
}
```

---

# 八、前端页面设计

## 1. 登录注册页面

页面包含：

```txt
1. 项目名称 LwChat
2. 用户名输入框
3. 密码输入框
4. 登录按钮
5. 注册入口
```

---

## 2. 主聊天页面

主页面采用三栏布局：

```txt
左侧：用户信息、私聊列表、群聊列表
中间：聊天窗口、消息输入框、图片上传按钮
右侧：用户资料、群成员列表、群公告
```

页面示意：

```txt
┌──────────────┬─────────────────────────┬──────────────┐
│ 会话列表      │ 聊天窗口                 │ 群信息/资料    │
│ 用户A         │                         │ 群公告         │
│ 用户B         │   对方消息               │ 群成员         │
│ 群聊1         │            我的消息      │ 管理按钮       │
│ 群聊2         │                         │              │
│              │ 输入框 + 图片 + 发送按钮 │              │
└──────────────┴─────────────────────────┴──────────────┘
```

---

# 九、本地运行方式

## 1. 启动后端

进入后端目录：

```bash
cd backend
```

安装依赖：

```bash
pip install -r requirements.txt
```

执行数据库迁移：

```bash
python manage.py makemigrations
python manage.py migrate
```

启动后端服务：

```bash
python manage.py runserver 8000
```

后端地址：

```txt
http://localhost:8000
```

WebSocket 地址：

```txt
ws://localhost:8000
```

---

## 2. 启动前端

进入前端目录：

```bash
cd frontend
```

安装依赖：

```bash
npm install
```

启动前端：

```bash
npm run dev
```

前端访问地址：

```txt
http://localhost:5173
```

---

# 十、演示方式

本项目可以直接在本地进行演示，不必须使用云服务器。

演示步骤如下：

```txt
1. 启动后端服务；
2. 启动前端服务；
3. 打开普通浏览器窗口，登录用户A；
4. 打开无痕窗口或另一个浏览器，登录用户B；
5. 用户A向用户B发送消息；
6. 用户B页面实时收到消息；
7. 用户B发送图片消息；
8. 用户A实时看到图片；
9. 创建群聊并发送群消息；
10. 展示群公告和群成员列表。
```

通过这种方式可以证明系统支持 WebSocket 实时通信。

如果需要多人异地访问，可以将项目部署到云服务器，并使用 Nginx 配置 HTTP 和 WebSocket 反向代理。

---

# 十一、项目特点

本项目具有以下特点：

```txt
1. 功能完整：包含注册登录、私聊、群聊、图片消息、群管理、离线消息等核心功能；
2. 技术清晰：前后端分离，HTTP 与 WebSocket 分工明确；
3. 易于演示：本地即可完成完整演示；
4. 易于扩展：后续可以继续增加好友系统、消息撤回、表情包、在线状态等功能；
5. 适合作业展示：结构完整，界面直观，功能容易说明。
```

---

# 十二、后续可扩展方向

后续可以继续扩展以下功能：

```txt
1. 好友申请与好友列表；
2. 消息撤回；
3. 表情包发送；
4. 在线状态显示；
5. 群管理员权限细化；
6. 消息已读未读状态；
7. 聊天记录搜索；
8. 语音消息；
9. 视频通话；
10. 云服务器部署与公网访问。
```

---

# 十三、项目总结

LwChat 聊天交互系统实现了一个 Web 聊天应用的基础功能。系统通过 Vue3 构建前端交互界面，通过 Django 提供后端接口服务，通过 SQLite 存储用户和消息数据，并使用 WebSocket 实现消息实时推送。

本项目虽然是一个简化版聊天系统，但已经覆盖了即时通信应用的核心流程，包括用户认证、消息发送、消息保存、实时接收、图片上传、群聊管理和离线消息加载等内容。

通过本项目，可以较完整地理解一个聊天系统从需求分析、数据库设计、接口设计、前后端交互到实时通信的实现过程。

---

# 十四、极简版项目定位

最后可以在报告里加一句很漂亮的总结：

> 本项目并不追求完整复刻商业级即时通信软件，而是以课程实践为目标，完成一个功能清晰、结构完整、可运行演示的轻量级 Web 聊天系统。

这个句子很关键。
它等于提前把老师的期待值框住：
**不是微信平替，是课程级 LwChat。**

这样文档体面，工程压力也不会炸锅。
小船不装航母发动机，但它要能稳稳开到岸边 🚢✨
