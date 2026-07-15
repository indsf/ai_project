<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import client from '../api/client'

const router = useRouter()
const posts = ref([])
const loading = ref(true)
const error = ref(null)

const categoryLabel = {
  festival: '축제',
  spot: '관광지',
  food: '맛집',
}

async function loadPosts() {
  loading.value = true
  error.value = null
  try {
    const res = await client.get('/posts')
    posts.value = res.data.items ?? res.data
  } catch (e) {
    error.value = '게시글을 불러오지 못했어요.'
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(loadPosts)
</script>

<template>
  <div class="page">
    <div class="header-row">
      <h1 class="page-title">게시판</h1>
      <button class="btn-primary" @click="router.push('/board/write')">글쓰기</button>
    </div>

    <div v-if="loading" class="state-msg">불러오는 중…</div>
    <div v-else-if="error" class="state-msg">{{ error }}</div>
    <div v-else-if="posts.length === 0" class="state-msg">
      아직 등록된 게시글이 없어요. 첫 글을 남겨보세요.
    </div>

    <div v-else class="post-list">
      <div
        v-for="post in posts"
        :key="post.id"
        class="card post-item"
        @click="router.push(`/board/${post.id}`)"
      >
        <div class="post-top">
          <span class="badge">{{ categoryLabel[post.category] || post.category }}</span>
          <span class="views">조회 {{ post.view_count ?? 0 }}</span>
        </div>
        <p class="post-title">{{ post.title }}</p>
        <p class="post-loc" v-if="post.location">{{ post.location }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.state-msg {
  color: var(--color-ink-soft);
  text-align: center;
  padding: 40px 0;
  font-size: 14px;
}
.post-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.post-item { cursor: pointer; }
.post-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.badge {
  background: var(--color-accent-soft);
  color: var(--color-accent);
  font-size: 12px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
}
.views {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--color-ink-soft);
}
.post-title {
  font-weight: 700;
  font-size: 15px;
  margin: 0 0 4px;
}
.post-loc {
  font-size: 13px;
  color: var(--color-ink-soft);
  margin: 0;
}
</style>