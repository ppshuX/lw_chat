<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

type User = {
  id: number
  username: string
  nickname: string
  avatar_text: string
}

type Group = {
  id: number
  name: string
  owner_id: number
  announcement: string
  member_count: number
  current_role: string
}

type Conversation = {
  type: 'private' | 'group'
  id: string
  target_id: number
  name: string
  avatar_text: string
  last_message: string
  last_time: string
  unread: number
  joined?: boolean
  peer?: User
  group?: Group
}

type Message = {
  id: number
  sender_id: number
  receiver_id?: number
  group_id?: number
  sender: User
  content: string
  message_type: 'text' | 'image'
  image_url: string
  created_at: string
}

type Member = {
  id: number
  user_id: number
  role: 'owner' | 'member'
  user: User
}

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const WS_BASE = API_BASE.replace(/^http/, 'ws')

const savedUser = localStorage.getItem('lwchat_user')
const currentUser = ref<User | null>(readSavedUser())
const authMode = ref<'login' | 'register'>('login')
const authForm = ref({ username: '', password: '', nickname: '' })
const authError = ref('')
const loading = ref(false)

const conversations = ref<Conversation[]>([])
const selected = ref<Conversation | null>(null)
const messages = ref<Message[]>([])
const members = ref<Member[]>([])
const messageText = ref('')
const groupName = ref('')
const noticeDraft = ref('')
const errorMessage = ref('')
const uploadLoading = ref(false)
const chatLoading = ref(false)
const messageListEl = ref<HTMLElement | null>(null)

let privateSocket: WebSocket | null = null
let groupSocket: WebSocket | null = null

const privateConversations = computed(() => conversations.value.filter((item) => item.type === 'private'))
const groupConversations = computed(() => conversations.value.filter((item) => item.type === 'group'))
const selectedGroup = computed(() => selected.value?.type === 'group' ? selected.value.group : null)
const selectedPeer = computed(() => selected.value?.type === 'private' ? selected.value.peer : null)
const isGroupOwner = computed(() => selectedGroup.value?.owner_id === currentUser.value?.id)

function readSavedUser() {
  if (!savedUser) return null
  try {
    return JSON.parse(savedUser) as User
  } catch {
    localStorage.removeItem('lwchat_user')
    return null
  }
}

function headers(json = true) {
  const base: Record<string, string> = {}
  if (json) base['Content-Type'] = 'application/json'
  if (currentUser.value) base['X-User-Id'] = String(currentUser.value.id)
  return base
}

async function api(path: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE}${path}`, options)
  const payload = await response.json()
  if (!response.ok) throw new Error(payload.message || '请求失败')
  return payload
}

function mediaUrl(url: string) {
  if (!url) return ''
  return url.startsWith('http') ? url : `${API_BASE}${url}`
}

function friendlyTime(value: string) {
  return value ? value.slice(11, 16) : ''
}

async function submitAuth() {
  authError.value = ''
  loading.value = true
  try {
    const path = authMode.value === 'login' ? '/api/login/' : '/api/register/'
    const payload = await api(path, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify(authForm.value),
    })
    currentUser.value = payload.data.user
    localStorage.setItem('lwchat_user', JSON.stringify(payload.data.user))
    await bootChat()
  } catch (error) {
    authError.value = error instanceof Error ? error.message : '操作失败'
  } finally {
    loading.value = false
  }
}

function logout() {
  closeSockets()
  currentUser.value = null
  selected.value = null
  conversations.value = []
  messages.value = []
  localStorage.removeItem('lwchat_user')
}

async function bootChat() {
  connectPrivateSocket()
  await loadConversations()
  const firstConversation = conversations.value[0]
  if (!selected.value && firstConversation) {
    await selectConversation(firstConversation)
  }
}

async function loadConversations() {
  if (!currentUser.value) return
  const payload = await api(`/api/conversations/?user_id=${currentUser.value.id}`, { headers: headers(false) })
  conversations.value = [...payload.data.private, ...payload.data.groups]
  if (selected.value) {
    const fresh = conversations.value.find((item) => item.id === selected.value?.id)
    if (fresh) selected.value = fresh
  }
}

async function selectConversation(conversation: Conversation) {
  errorMessage.value = ''
  chatLoading.value = true
  selected.value = conversation
  messages.value = []
  members.value = []
  try {
    if (!currentUser.value) return

    if (conversation.type === 'private') {
      closeGroupSocket()
      const payload = await api(
        `/api/private-messages/?user_id=${currentUser.value.id}&peer_id=${conversation.target_id}`,
        { headers: headers(false) },
      )
      messages.value = payload.data
    } else {
      if (!conversation.joined) {
        await joinGroup(conversation)
      }
      const [messagePayload, memberPayload] = await Promise.all([
        api(`/api/group-messages/?group_id=${conversation.target_id}`, { headers: headers(false) }),
        api(`/api/groups/${conversation.target_id}/members/`, { headers: headers(false) }),
      ])
      messages.value = messagePayload.data
      members.value = memberPayload.data
      noticeDraft.value = conversation.group?.announcement || ''
      connectGroupSocket(conversation.target_id)
    }
    await loadConversations()
    scrollToBottom()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '会话加载失败'
  } finally {
    chatLoading.value = false
  }
}

async function createGroup() {
  const name = groupName.value.trim()
  if (!name) return
  try {
    const payload = await api('/api/groups/', {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ name }),
    })
    groupName.value = ''
    await loadConversations()
    const created = conversations.value.find((item) => item.type === 'group' && item.target_id === payload.data.id)
    if (created) await selectConversation(created)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '创建群聊失败'
  }
}

async function joinGroup(conversation: Conversation) {
  const payload = await api(`/api/groups/${conversation.target_id}/join/`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({}),
  })
  conversation.joined = true
  conversation.group = payload.data
}

async function updateAnnouncement() {
  if (!selectedGroup.value) return
  try {
    const payload = await api(`/api/groups/${selectedGroup.value.id}/announcement/`, {
      method: 'PUT',
      headers: headers(),
      body: JSON.stringify({ announcement: noticeDraft.value }),
    })
    if (selected.value?.group) selected.value.group = payload.data
    await loadConversations()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '公告更新失败'
  }
}

async function removeMember(member: Member) {
  if (!selectedGroup.value || member.role === 'owner') return
  try {
    await api(`/api/groups/${selectedGroup.value.id}/members/${member.id}/`, {
      method: 'DELETE',
      headers: headers(false),
    })
    members.value = members.value.filter((item) => item.id !== member.id)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '移除成员失败'
  }
}

function sendText() {
  const content = messageText.value.trim()
  if (!content) return
  sendMessage('text', content, '')
  messageText.value = ''
}

function sendMessage(messageType: 'text' | 'image', content: string, imageUrl: string) {
  if (!selected.value || !currentUser.value) return
  const payload = {
    sender_id: currentUser.value.id,
    receiver_id: selected.value.type === 'private' ? selected.value.target_id : undefined,
    group_id: selected.value.type === 'group' ? selected.value.target_id : undefined,
    message_type: messageType,
    content,
    image_url: imageUrl,
  }
  const socket = selected.value.type === 'private' ? privateSocket : groupSocket
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(payload))
  } else {
    errorMessage.value = 'WebSocket 未连接，请刷新后重试'
  }
}

async function uploadImage(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  uploadLoading.value = true
  errorMessage.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file)
    const payload = await api('/api/upload-image/', {
      method: 'POST',
      headers: headers(false),
      body: formData,
    })
    sendMessage('image', payload.data.url, payload.data.url)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '图片上传失败'
  } finally {
    input.value = ''
    uploadLoading.value = false
  }
}

function connectPrivateSocket() {
  if (!currentUser.value) return
  if (privateSocket) privateSocket.close()
  privateSocket = new WebSocket(`${WS_BASE}/ws/private/${currentUser.value.id}/`)
  privateSocket.onerror = () => {
    errorMessage.value = '私聊连接异常，请确认后端服务已启动'
  }
  privateSocket.onmessage = async (event) => {
    const payload = JSON.parse(event.data)
    if (payload.type !== 'private_message') return
    const message: Message = payload.message
    const active = selected.value?.type === 'private'
      && (selected.value.target_id === message.sender_id || selected.value.target_id === message.receiver_id)
    if (active && !messages.value.some((item) => item.id === message.id)) {
      messages.value.push(message)
      scrollToBottom()
    }
    await loadConversations()
  }
}

function connectGroupSocket(groupId: number) {
  closeGroupSocket()
  groupSocket = new WebSocket(`${WS_BASE}/ws/group/${groupId}/`)
  groupSocket.onerror = () => {
    errorMessage.value = '群聊连接异常，请确认后端服务已启动'
  }
  groupSocket.onmessage = async (event) => {
    const payload = JSON.parse(event.data)
    if (payload.type !== 'group_message') return
    const message: Message = payload.message
    if (selected.value?.type === 'group' && selected.value.target_id === message.group_id) {
      if (!messages.value.some((item) => item.id === message.id)) {
        messages.value.push(message)
        scrollToBottom()
      }
    }
    await loadConversations()
  }
}

function closeGroupSocket() {
  if (groupSocket) {
    groupSocket.close()
    groupSocket = null
  }
}

function closeSockets() {
  if (privateSocket) privateSocket.close()
  closeGroupSocket()
}

async function scrollToBottom() {
  await nextTick()
  if (messageListEl.value) {
    messageListEl.value.scrollTop = messageListEl.value.scrollHeight
  }
}

onMounted(() => {
  if (currentUser.value) bootChat()
})

onBeforeUnmount(() => closeSockets())
</script>

<template>
  <main v-if="!currentUser" class="auth-page">
    <section class="auth-panel">
      <div class="brand-mark">Lw</div>
      <h1>LwChat</h1>
      <p>课程作业级轻量聊天系统</p>

      <form class="auth-form" @submit.prevent="submitAuth">
        <input v-model.trim="authForm.username" placeholder="用户名" autocomplete="username" />
        <input v-model="authForm.password" placeholder="密码" type="password" autocomplete="current-password" />
        <input
          v-if="authMode === 'register'"
          v-model.trim="authForm.nickname"
          placeholder="昵称"
          autocomplete="nickname"
        />
        <button type="submit" :disabled="loading">{{ loading ? '处理中...' : authMode === 'login' ? '登录' : '注册' }}</button>
      </form>

      <p v-if="authError" class="notice error">{{ authError }}</p>
      <button class="link-button" @click="authMode = authMode === 'login' ? 'register' : 'login'">
        {{ authMode === 'login' ? '没有账号？注册一个' : '已有账号？返回登录' }}
      </button>
    </section>
  </main>

  <main v-else class="chat-shell">
    <aside class="sidebar">
      <div class="profile-row">
        <div class="avatar self">{{ currentUser.avatar_text }}</div>
        <div class="profile-main">
          <strong>{{ currentUser.nickname }}</strong>
          <span>@{{ currentUser.username }}</span>
        </div>
        <button class="ghost-button" @click="logout">退出</button>
      </div>

      <div class="group-create">
        <input v-model.trim="groupName" placeholder="新建群聊名称" @keyup.enter="createGroup" />
        <button @click="createGroup">创建</button>
      </div>

      <div class="conversation-section">
        <div class="section-title">私聊</div>
        <div v-if="privateConversations.length === 0" class="list-empty">暂无其他用户</div>
        <button
          v-for="item in privateConversations"
          :key="item.id"
          class="conversation-item"
          :class="{ active: selected?.id === item.id }"
          @click="selectConversation(item)"
        >
          <div class="avatar">{{ item.avatar_text }}</div>
          <div class="conversation-main">
            <div class="conversation-top">
              <strong>{{ item.name }}</strong>
              <span>{{ item.last_time }}</span>
            </div>
            <div class="conversation-bottom">
              <span>{{ item.last_message }}</span>
              <em v-if="item.unread">{{ item.unread }}</em>
            </div>
          </div>
        </button>
      </div>

      <div class="conversation-section">
        <div class="section-title">群聊</div>
        <div v-if="groupConversations.length === 0" class="list-empty">还没有群聊</div>
        <button
          v-for="item in groupConversations"
          :key="item.id"
          class="conversation-item"
          :class="{ active: selected?.id === item.id }"
          @click="selectConversation(item)"
        >
          <div class="avatar group">{{ item.avatar_text }}</div>
          <div class="conversation-main">
            <div class="conversation-top">
              <strong>{{ item.name }}</strong>
              <span>{{ item.last_time }}</span>
            </div>
            <div class="conversation-bottom">
              <span>{{ item.joined ? item.last_message : '未加入，点击加入' }}</span>
            </div>
          </div>
        </button>
      </div>
    </aside>

    <section class="chat-panel">
      <header class="chat-header">
        <div>
          <h2>{{ selected?.name || '选择一个会话' }}</h2>
          <p v-if="selected?.type === 'group'">{{ selected.group?.member_count || members.length }} 位成员</p>
          <p v-else-if="selectedPeer">私聊会话</p>
        </div>
      </header>

      <div ref="messageListEl" class="message-list">
        <div v-if="!selected" class="empty-state">
          <strong>选择一个会话，开始聊天</strong>
          <span>可以进行私聊，也可以创建群聊邀请同学加入。</span>
        </div>
        <div v-else-if="chatLoading" class="empty-state">
          <strong>正在加载消息</strong>
          <span>请稍候。</span>
        </div>
        <div v-else-if="messages.length === 0" class="empty-state">
          <strong>还没有消息</strong>
          <span>发送第一条消息，或上传一张图片。</span>
        </div>
        <div
          v-for="message in messages"
          :key="message.id"
          class="message-row"
          :class="{ mine: message.sender_id === currentUser.id }"
        >
          <div class="avatar tiny">{{ message.sender.avatar_text }}</div>
          <div class="bubble-wrap">
            <div class="message-meta">
              <span>{{ message.sender.nickname }}</span>
              <span>{{ friendlyTime(message.created_at) }}</span>
            </div>
            <div class="bubble" :class="{ image: message.message_type === 'image' }">
              <img v-if="message.message_type === 'image'" :src="mediaUrl(message.image_url || message.content)" alt="聊天图片" />
              <span v-else>{{ message.content }}</span>
            </div>
          </div>
        </div>
      </div>

      <footer class="composer" :class="{ idle: !selected }">
        <p v-if="errorMessage" class="notice error">{{ errorMessage }}</p>
        <p v-if="!selected" class="composer-hint">选择一个会话后即可发送文本或图片。</p>
        <div class="composer-actions">
          <label class="icon-button" :class="{ disabled: uploadLoading || !selected }" title="发送图片">
            {{ uploadLoading ? '上传中' : '图片' }}
            <input type="file" accept="image/*" :disabled="uploadLoading || !selected" @change="uploadImage" />
          </label>
          <textarea
            v-model="messageText"
            :disabled="!selected"
            placeholder="输入消息，按 Enter 发送"
            @keydown.enter.exact.prevent="sendText"
          />
          <button class="send-button" :disabled="!selected || !messageText.trim()" @click="sendText">发送</button>
        </div>
      </footer>
    </section>

    <aside class="info-panel">
      <template v-if="selectedPeer">
        <div class="info-card">
          <div class="avatar large">{{ selectedPeer.avatar_text }}</div>
          <h3>{{ selectedPeer.nickname }}</h3>
          <p>@{{ selectedPeer.username }}</p>
        </div>
        <div class="info-block">
          <h4>会话说明</h4>
          <p>一对一私聊支持文本和图片消息，刷新后可继续加载历史记录。</p>
        </div>
      </template>

      <template v-else-if="selectedGroup">
        <div class="info-card">
          <div class="avatar large group">{{ selectedGroup.name.slice(0, 1).toUpperCase() }}</div>
          <h3>{{ selectedGroup.name }}</h3>
          <p>{{ selectedGroup.member_count || members.length }} 位成员</p>
        </div>
        <div class="info-block">
          <div class="info-heading">
            <h4>群公告</h4>
            <span v-if="isGroupOwner">群主可编辑</span>
          </div>
          <textarea v-if="isGroupOwner" v-model="noticeDraft" class="notice-editor" />
          <p v-else>{{ selectedGroup.announcement || '暂无公告' }}</p>
          <button v-if="isGroupOwner" class="secondary-button" @click="updateAnnouncement">保存公告</button>
        </div>
        <div class="info-block">
          <div class="info-heading">
            <h4>群成员</h4>
            <span>{{ members.length }}</span>
          </div>
          <div class="member-list">
            <div v-for="member in members" :key="member.id" class="member-item">
              <div class="avatar tiny">{{ member.user.avatar_text }}</div>
              <div>
                <strong>{{ member.user.nickname }}</strong>
                <span>{{ member.role === 'owner' ? '群主' : '成员' }}</span>
              </div>
              <button
                v-if="isGroupOwner && member.role !== 'owner'"
                class="text-danger"
                @click="removeMember(member)"
              >
                移除
              </button>
            </div>
          </div>
        </div>
      </template>

      <div v-else class="info-block muted">
        <h4>会话信息</h4>
        <p>选中一个私聊或群聊后，这里会显示对方资料、群公告和成员列表。</p>
      </div>
    </aside>
  </main>
</template>
