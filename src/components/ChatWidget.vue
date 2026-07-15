<script setup>
import { ref, nextTick } from 'vue'
import client from '../api/client'
import { chatState } from '../stores/chatState'

const messages = chatState.messages
const input = ref('')
const sending = ref(false)
const open = ref(false)
const scrollBox = ref(null)

function toggle() {
  open.value = !open.value
}

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return

  messages.push({ role: 'user', content: text })
  input.value = ''
  sending.value = true

  await scrollToBottom()

  try {
    const history = messages.slice(0, -1).map((m) => ({ role: m.role, content: m.content }))
    const res = await client.post('/chat', { message: text, history })
    messages.push({ role: 'assistant', content: res.data.reply })
  } catch (e) {
    messages.push({ role: 'assistant', content: '답변을 가져오지 못했어요. 잠시 후 다시 시도해주세요.' })
    console.error(e)
  } finally {
    sending.value = false
    await scrollToBottom()
  }
}

async function scrollToBottom() {
  await nextTick()
  if (scrollBox.value) scrollBox.value.scrollTop = scrollBox.value.scrollHeight
}
</script>

<template>
  <button class="chat-fab" :class="{ 'is-open': open }" @click="toggle" aria-label="챗봇 열기">
    {{ open ? '✕' : '🦝' }}
  </button>

  <div class="chat-panel" :class="{ 'is-open': open }">
    <div class="chat-head">
      <div class="chat-avatar">🦝</div>
      <div class="chat-head-text">
        <div class="name">오구 · AI 메이트</div>
        <div class="status"><span class="dot"></span>지금 답변 가능</div>
      </div>
    </div>

    <div class="chat-body" ref="scrollBox">
      <div
        v-for="(m, i) in messages"
        :key="i"
        class="bubble"
        :class="m.role === 'user' ? 'user' : 'bot'"
      >{{ m.content }}</div>
      <div v-if="sending" class="bubble bot">생각 중…</div>
    </div>

    <div class="chat-input">
      <input v-model="input" type="text" placeholder="구미에 대해 뭐든 물어봐" @keyup.enter="send" />
      <button @click="send" :disabled="sending" aria-label="전송">→</button>
    </div>
  </div>
</template>

<style scoped>
.chat-fab {
  position: fixed;
  right: 20px;
  bottom: 88px;
  z-index: 100;
  width: 58px;
  height: 58px;
  border-radius: 50%;
  background: var(--color-chat);
  border: 2.5px solid var(--color-line);
  box-shadow: 4px 4px 0 var(--color-line);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}
@media (min-width: 900px) {
  .chat-fab { bottom: 24px; }
}
.chat-fab.is-open { background: var(--color-ink); color: #fff; }

.chat-panel {
  position: fixed;
  right: 16px;
  bottom: 156px;
  left: 16px;
  z-index: 100;
  max-width: 340px;
  margin-left: auto;
  background: #fff;
  border: 2.5px solid var(--color-line);
  border-radius: var(--radius);
  box-shadow: 6px 6px 0 var(--color-line);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  opacity: 0;
  transform: translateY(12px) scale(0.97);
  pointer-events: none;
  transition: opacity 0.18s ease, transform 0.18s ease;
}
@media (min-width: 900px) {
  .chat-panel { bottom: 92px; right: 24px; left: auto; }
}
.chat-panel.is-open { opacity: 1; transform: translateY(0) scale(1); pointer-events: auto; }

.chat-head {
  background: var(--color-chat-soft);
  padding: 14px 16px;
  border-bottom: 2.5px solid var(--color-line);
  display: flex;
  align-items: center;
  gap: 10px;
}
.chat-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--color-chat); border: 2px solid var(--color-line);
  display: flex; align-items: center; justify-content: center; font-size: 15px;
}
.chat-head-text { flex: 1; }
.name { font-weight: 800; font-size: 14px; }
.status { font-size: 11px; color: var(--color-ink-soft); display: flex; align-items: center; gap: 5px; }
.status .dot { width: 6px; height: 6px; border-radius: 50%; background: #33C86B; }

.chat-body {
  padding: 14px; display: flex; flex-direction: column; gap: 9px;
  max-height: 320px; overflow-y: auto;
}
.bubble {
  max-width: 85%; padding: 9px 12px; border-radius: 14px;
  font-size: 13px; font-weight: 500; line-height: 1.5; white-space: pre-wrap;
}
.bubble.bot { background: var(--color-chat-soft); border: 2px solid var(--color-line); align-self: flex-start; border-bottom-left-radius: 4px; }
.bubble.user { background: var(--color-ink); color: #fff; align-self: flex-end; border-bottom-right-radius: 4px; }

.chat-input { display: flex; gap: 8px; padding: 12px; border-top: 2.5px solid var(--color-line); }
.chat-input input {
  flex: 1; border: 2px solid var(--color-line); border-radius: 999px;
  padding: 9px 14px; font-size: 13px; outline: none;
}
.chat-input button {
  background: var(--color-accent); border: 2px solid var(--color-line); border-radius: 50%;
  width: 36px; height: 36px; font-size: 15px; flex-shrink: 0;
}
</style>
