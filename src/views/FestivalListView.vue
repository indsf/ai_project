<script setup>
import { ref, onMounted } from 'vue'
import client from '../api/client'
const festivals = ref([])
const loading = ref(true)
const search = ref('')
async function loadFestivals() {
  loading.value = true
  try {
    const res = await client.get('/places/festivals', { params: { search: search.value || undefined, page: 1, size: 30 } })
    festivals.value = res.data.items
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}
onMounted(loadFestivals)
</script>
<template>
  <div class="page">
    <h1 class="page-title">구미 근처 축제</h1>
    <div class="search-row">
      <input v-model="search" type="text" placeholder="축제 이름 검색" @keyup.enter="loadFestivals" />
      <button class="btn-primary" @click="loadFestivals">검색</button>
    </div>
    <div v-if="loading" class="state-msg">불러오는 중…</div>
    <div v-else-if="festivals.length === 0" class="state-msg">검색 결과가 없어요.</div>
    <div v-else class="festival-grid">
      <div v-for="f in festivals" :key="f.content_id" class="card festival-item">
        <img v-if="f.image_url" :src="f.image_url" class="thumb" alt="" />
        <div class="thumb placeholder" v-else>이미지 없음</div>
        <p class="f-title">{{ f.title }}</p>
        <p class="f-addr">{{ f.addr1 }}</p>
      </div>
    </div>
  </div>
</template>
<style scoped>
.search-row {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.search-row input {
  flex: 1;
  border: 1px solid var(--color-line);
  border-radius: 8px;
  padding: 10px 12px;
}
.state-msg {
  color: var(--color-ink-soft);
  text-align: center;
  padding: 40px 0;
}
.festival-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
@media (min-width: 900px) {
  .festival-grid { grid-template-columns: 1fr 1fr 1fr; }
}
.festival-item { padding: 0; overflow: hidden; }
.thumb {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  display: block;
}
.thumb.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-line);
  color: var(--color-ink-soft);
  font-size: 12px;
}
.f-title {
  font-weight: 700;
  font-size: 13px;
  margin: 8px 10px 2px;
}
.f-addr {
  font-size: 11px;
  color: var(--color-ink-soft);
  margin: 0 10px 10px;
}
</style>