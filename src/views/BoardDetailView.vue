<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import client from '../api/client'

const props = defineProps({ id: String })
const router = useRouter()

const post = ref(null)
const loading = ref(true)
const deletePassword = ref('')
const showDeleteBox = ref(false)
const deleteError = ref(null)

const categoryLabel = { festival: '축제', spot: '관광지', food: '맛집' }

async function loadPost() {
  loading.value = true
  try {
    const res = await client.get(`/posts/${props.id}`)
    post.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function confirmDelete() {
  if (!deletePassword.value.trim()) {
    deleteError.value = '비밀번호를 입력해주세요.'
    return
  }
  try {
    await client.delete(`/posts/${props.id}`, { params: { password: deletePassword.value } })
    router.push('/board')
  } catch (e) {
    deleteError.value = '비밀번호가 틀렸거나 삭제에 실패했어요.'
  }
}

onMounted(loadPost)
</script>

<template>
  <div class="page">
    <div v-if="loading" class="state-msg">불러오는 중…</div>

    <template v-else-if="post">
      <span class="badge">{{ categoryLabel[post.category] || post.category }}</span>
      <h1 class="post-title">{{ post.title }}</h1>
      <p class="meta" v-if="post.location">{{ post.location }}</p>
      <p class="meta" v-if="post.start_date">{{ post.start_date }} ~ {{ post.end_date || '' }}</p>

      <div class="card content-box">{{ post.content }}</div>

      <div class="actions">
        <button class="btn-secondary" @click="router.push('/board')">목록으로</button>
        <button class="btn-secondary danger" @click="showDeleteBox = !showDeleteBox">삭제</button>
      </div>

      <div v-if="showDeleteBox" class="delete-box">
        <input v-model="deletePassword" type="password" placeholder="비밀번호 입력" />
        <button class="btn-primary" @click="confirmDelete">삭제 확인</button>
        <p v-if="deleteError" class="error-msg">{{ deleteError }}</p>
      </div>
    </template>

    <div v-else class="state-msg">게시글을 찾을 수 없어요.</div>
  </div>
</template>

<style scoped>
.state-msg {
  color: var(--color-ink-soft);
  text-align: center;
  padding: 40px 0;
}
.badge {
  background: var(--color-accent-soft);
  color: var(--color-accent);
  font-size: 12px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
}
.post-title {
  font-size: 20px;
  font-weight: 800;
  margin: 10px 0 4px;
}
.meta {
  font-size: 13px;
  color: var(--color-ink-soft);
  margin: 2px 0;
}
.content-box {
  margin-top: 16px;
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 14px;
}
.actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}
.btn-secondary {
  flex: 1;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: 10px;
  padding: 12px;
  font-weight: 700;
  font-size: 14px;
}
.btn-secondary.danger { color: #D64545; }
.delete-box {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.delete-box input {
  border: 1px solid var(--color-line);
  border-radius: 8px;
  padding: 10px 12px;
}
.error-msg { color: #D64545; font-size: 13px; margin: 0; }
</style>