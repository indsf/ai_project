<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import client from '../api/client'

const router = useRouter()

const weather = ref(null)
const weatherLoading = ref(true)
const recPlaces = ref([])
const recLoading = ref(true)
const indexCounts = ref([])
const posts = ref([])

const CATEGORY_META = [
  { slug: 'festivals', label: '축제·공연' },
  { slug: 'attractions', label: '관광지' },
  { slug: 'restaurants', label: '음식점' },
  { slug: 'leisure', label: '레포츠' },
  { slug: 'culture', label: '문화시설' },
  { slug: 'lodging', label: '숙박' },
  { slug: 'courses', label: '여행코스' },
  { slug: 'shopping', label: '쇼핑' },
]

const WEATHER_LABEL = {
  sunny: (t) => `맑음 ${Math.round(t)}°C ☀️`,
  rain: (t) => `비 ${Math.round(t)}°C 🌧️`,
  hot: (t) => `무더움 ${Math.round(t)}°C 🥵`,
  cold: (t) => `쌀쌀함 ${Math.round(t)}°C ❄️`,
}
const WEATHER_TAGS = {
  sunny: ['outdoor', 'sunny'],
  rain: ['indoor', 'rain'],
  hot: ['hot'],
  cold: ['cold'],
}

const TAG_LABEL = {
  indoor: '실내',
  outdoor: '실외',
  rain: '우천 가능',
  hot: '더운 날 추천',
  cold: '추운 날 추천',
  sunny: '맑은 날 추천',
  any_weather: '날씨 무관',
}

function weatherCategory(f) {
  if (!f) return 'sunny'
  if (['RAIN', 'RAIN_SNOW', 'SHOWER', 'SNOW'].includes(f.rain_type)) return 'rain'
  if (f.temperature >= 33) return 'hot'
  if (f.temperature <= 0) return 'cold'
  return 'sunny'
}

async function loadWeatherAndRecs() {
  weatherLoading.value = true
  recLoading.value = true
  try {
    const res = await client.get('/weather/current')
    weather.value = res.data

    const cat = weatherCategory(res.data)
    const tags = WEATHER_TAGS[cat]

    const recRes = await client.get('/places', {
      params: {
        category: CATEGORY_META.map((c) => c.slug).join(','),
        tags: tags.join(','),
        match: 'any',
        page: 1,
        size: 6,
      },
    })
    recPlaces.value = recRes.data.items
  } catch (e) {
    console.error('weather/rec load error', e)
  } finally {
    weatherLoading.value = false
    recLoading.value = false
  }
}

async function loadIndexCounts() {
  const results = await Promise.all(
    CATEGORY_META.map(async (c) => {
      try {
        const res = await client.get(`/places/${c.slug}`, { params: { page: 1, size: 1 } })
        return { ...c, count: res.data.total }
      } catch {
        return { ...c, count: 0 }
      }
    })
  )
  indexCounts.value = results
}

async function loadCommunity() {
  try {
    const res = await client.get('/posts', { params: { page: 1, size: 3 } })
    posts.value = res.data.items ?? res.data
  } catch (e) {
    console.error('community load error', e)
  }
}

const weatherLabelText = () => {
  if (weatherLoading.value || !weather.value) return '날씨 불러오는 중...'
  const cat = weatherCategory(weather.value)
  return WEATHER_LABEL[cat](weather.value.temperature)
}

onMounted(() => {
  loadWeatherAndRecs()
  loadIndexCounts()
  loadCommunity()
})
</script>

<template>
  <section class="hero">
    <div class="weather-pill" :class="{ 'is-loading': weatherLoading }">
      <span class="live-dot"></span>
      <span class="value">{{ weatherLabelText() }}</span>
      <span class="sub">LIVE</span>
    </div>
    <h1>오늘 구미,<br /><span class="hi">뭐하지?</span></h1>
    <p>지금 날씨 보고 골라드림. 딱히 고민 안 해도 됨 🙆</p>
    <p class="note">실시간 기상 데이터 기준 자동 추천</p>
  </section>

  <section class="rec-section">
    <div v-if="recLoading" class="state-msg">추천 불러오는 중…</div>
    <div v-else-if="recPlaces.length === 0" class="state-msg">지금 조건에 맞는 추천이 없어요.</div>
    <div v-else class="rec-grid">
      <article v-for="p in recPlaces" :key="p.content_id" class="card rec-card">
        <div class="rec-top">
          <span class="cat-chip">{{ CATEGORY_META.find((c) => c.slug === p.category)?.label || p.category }}</span>
          <span v-if="p.distance_km" class="rec-dist">{{ p.distance_km }}km</span>
        </div>
        <h3>{{ p.title }}</h3>
        <p class="addr">{{ p.addr1 || '주소 미정' }}</p>
        <div class="rec-tags">
          <span v-for="t in p.tags" :key="t" class="tag">{{ TAG_LABEL[t] || t }}</span>
        </div>
      </article>
    </div>
  </section>

  <section class="index-section">
    <div class="section-head">
      <h2>전체 색인</h2>
      <div class="total">한국관광공사 TourAPI · 총 <strong>{{ indexCounts.reduce((a, c) => a + c.count, 0) }}</strong>건 수록</div>
    </div>
    <div class="index-list">
      <router-link
        v-for="c in indexCounts"
        :key="c.slug"
        :to="`/festivals?category=${c.slug}`"
        class="index-item"
      >
        <div class="label">{{ c.label }}</div>
        <div class="count">{{ c.count }}</div>
      </router-link>
    </div>
  </section>

  <section class="community-section">
    <div class="section-head">
      <h2>커뮤니티</h2>
      <a class="more-link" @click="router.push('/board')">전체 글 보기 →</a>
    </div>
    <div v-if="posts.length === 0" class="state-msg">아직 등록된 게시글이 없어요.</div>
    <div v-else class="post-grid">
      <article
        v-for="p in posts"
        :key="p.id"
        class="post-card"
        @click="router.push(`/board/${p.id}`)"
      >
        <span class="post-chip" :data-cat="p.category">{{ p.category }}</span>
        <h3>{{ p.title }}</h3>
        <p>{{ p.location || '위치 미정' }}</p>
        <div class="post-meta">
          <span>{{ p.location || '-' }}</span>
          <span>조회 {{ p.view_count ?? 0 }}</span>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.hero { padding: 40px 16px 24px; }
.weather-pill {
  display: inline-flex; align-items: center; gap: 8px;
  background: #fff; border: 2.5px solid var(--color-line);
  border-radius: 999px; padding: 8px 16px 8px 12px;
  font-weight: 700; font-size: 13px;
  box-shadow: 3px 3px 0 var(--color-line);
  margin-bottom: 18px;
}
.live-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--color-accent); animation: pulse 1.6s ease-in-out infinite; }
@keyframes pulse { 0%,100%{ opacity:1; transform:scale(1);} 50%{ opacity:0.4; transform:scale(0.75);} }
.sub { font-family: var(--font-mono); font-weight: 500; color: var(--color-ink-faint); font-size: 10px; }
.is-loading .value { color: var(--color-ink-faint); }

h1 { font-family: var(--font-display); font-weight: 400; font-size: 36px; line-height: 1.2; margin: 0 0 12px; }
.hi { color: var(--color-accent); }
.hero p { font-size: 15px; color: var(--color-ink-soft); margin: 0 0 6px; font-weight: 500; }
.hero .note { font-size: 12px; color: var(--color-ink-faint); margin: 0; }

.rec-section { padding: 8px 16px 36px; }
.state-msg { color: var(--color-ink-soft); text-align: center; padding: 30px 0; font-size: 14px; }
.rec-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (min-width: 900px) { .rec-grid { grid-template-columns: repeat(3, 1fr); } }
.rec-card { display: flex; flex-direction: column; gap: 8px; }
.rec-top { display: flex; align-items: center; justify-content: space-between; }
.cat-chip {
  font-weight: 800; font-size: 10.5px; padding: 3px 8px; border-radius: 999px;
  border: 2px solid var(--color-line); background: var(--color-lime-soft);
}
.rec-dist { font-family: var(--font-mono); font-size: 11px; color: var(--color-ink-faint); }
.rec-card h3 { font-size: 15px; font-weight: 800; margin: 0; }
.rec-card .addr { font-size: 11.5px; color: var(--color-ink-soft); margin: 0; }
.rec-tags { display: flex; gap: 5px; flex-wrap: wrap; margin-top: auto; }
.tag { font-size: 10px; font-family: var(--font-mono); color: var(--color-ink-soft); border: 1.5px solid var(--color-line); border-radius: 6px; padding: 2px 6px; }

.index-section, .community-section { padding: 32px 16px; border-top: 2.5px solid var(--color-line); }
.section-head { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 18px; flex-wrap: wrap; gap: 8px; }
.section-head h2 { font-family: var(--font-display); font-weight: 400; font-size: 22px; margin: 0; }
.total { font-family: var(--font-mono); font-size: 11px; color: var(--color-ink-faint); }
.total strong { color: var(--color-chat); font-weight: 700; }

.index-list { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
@media (min-width: 900px) { .index-list { grid-template-columns: repeat(4, 1fr); } }
.index-item {
  display: block; background: #fff; border: 2.5px solid var(--color-line);
  border-radius: var(--radius-s); padding: 14px 16px; box-shadow: 3px 3px 0 var(--color-line);
}
.index-item .label { font-size: 12.5px; font-weight: 700; margin-bottom: 4px; }
.index-item .count { font-family: var(--font-mono); font-size: 20px; color: var(--color-chat); font-weight: 600; }

.more-link { font-size: 13px; font-weight: 700; color: var(--color-accent); }

.post-grid { display: flex; flex-direction: column; gap: 12px; }
@media (min-width: 900px) { .post-grid { display: grid; grid-template-columns: repeat(3, 1fr); } }
.post-card { background: #fff; border: 2.5px solid var(--color-line); border-radius: var(--radius); padding: 16px; box-shadow: 3px 3px 0 var(--color-line); cursor: pointer; }
.post-chip { display: inline-block; font-weight: 800; font-size: 10.5px; padding: 3px 9px; border-radius: 999px; border: 2px solid var(--color-line); margin-bottom: 10px; background: var(--color-sky-soft); }
.post-chip[data-cat="festival"] { background: var(--color-accent-soft); }
.post-chip[data-cat="spot"] { background: var(--color-lime-soft); }
.post-card h3 { font-size: 15px; font-weight: 800; margin: 0 0 6px; }
.post-card p { font-size: 12.5px; color: var(--color-ink-soft); margin: 0 0 12px; }
.post-meta { display: flex; justify-content: space-between; font-family: var(--font-mono); font-size: 10.5px; color: var(--color-ink-faint); border-top: 1.5px dashed var(--color-line); padding-top: 10px; }
</style>