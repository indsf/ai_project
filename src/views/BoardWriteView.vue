<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import client from '../api/client'

const router = useRouter()

const form = ref({
  title: '',
  content: '',
  category: 'festival',
  indoor_outdoor: 'outdoor',
  location: '',
  start_date: '',
  end_date: '',
  password: '',
})

const submitting = ref(false)
const error = ref(null)

async function submit() {
  if (!form.value.title.trim() || !form.value.content.trim() || !form.value.password.trim()) {
    error.value = '제목, 내용, 비밀번호는 필수예요.'
    return
  }
  submitting.value = true
  error.value = null
  try {
    await client.post('/posts', form.value)
    router.push('/board')
  } catch (e) {
    error.value = '등록에 실패했어요. 잠시 후 다시 시도해주세요.'
    console.error(e)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page">
    <h1 class="page-title">글쓰기</h1>

    <div class="form">
      <label class="field">
        <span class="field-label">제목</span>
        <input v-model="form.title" type="text" placeholder="제목을 입력하세요" />
      </label>

      <label class="field">
        <span class="field-label">카테고리</span>
        <select v-model="form.category">
          <option value="festival">축제</option>
          <option value="spot">관광지</option>
          <option value="food">맛집</option>
        </select>
      </label>

      <label class="field">
        <span class="field-label">실내/실외</span>
        <select v-model="form.indoor_outdoor">
          <option value="indoor">실내</option>
          <option value="outdoor">실외</option>
          <option value="both">둘 다</option>
        </select>
      </label>

      <label class="field">
        <span class="field-label">위치</span>
        <input v-model="form.location" type="text" placeholder="예: 구미시 원평동" />
      </label>

      <div class="date-row">
        <label class="field">
          <span class="field-label">시작일</span>
          <input v-model="form.start_date" type="date" />
        </label>
        <label class="field">
          <span class="field-label">종료일</span>
          <input v-model="form.end_date" type="date" />
        </label>
      </div>

      <label class="field">
        <span class="field-label">내용</span>
        <textarea v-model="form.content" rows="6" placeholder="내용을 입력하세요"></textarea>
      </label>

      <label class="field">
        <span class="field-label">비밀번호 (수정/삭제 시 필요)</span>
        <input v-model="form.password" type="password" placeholder="비밀번호" />
      </label>

      <p v-if="error" class="error-msg">{{ error }}</p>

      <button class="btn-primary btn-block" :disabled="submitting" @click="submit">
        {{ submitting ? '등록 중…' : '등록하기' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-ink-soft);
}
input, select, textarea {
  border: 1px solid var(--color-line);
  border-radius: 8px;
  padding: 10px 12px;
  background: var(--color-surface);
}
textarea { resize: vertical; }
.date-row {
  display: flex;
  gap: 10px;
}
.date-row .field { flex: 1; }
.btn-block { width: 100%; margin-top: 8px; }
.error-msg {
  color: #D64545;
  font-size: 13px;
  margin: 0;
}
</style>