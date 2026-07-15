<script setup>
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const tabs = [
  { path: '/', label: '홈', icon: '🏠' },
  { path: '/festivals', label: '축제·관광', icon: '🎪' },
  { path: '/board', label: '커뮤니티', icon: '📋' },
]

function isActive(path) {
  return path === '/' ? route.path === '/' : route.path.startsWith(path)
}
</script>

<template>
  <nav class="bottom-nav">
    <button
      v-for="tab in tabs"
      :key="tab.path"
      class="tab"
      :class="{ active: isActive(tab.path) }"
      @click="router.push(tab.path)"
    >
      <span class="icon">{{ tab.icon }}</span>
      <span class="label">{{ tab.label }}</span>
    </button>
  </nav>
</template>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 480px;
  display: flex;
  background: var(--color-surface);
  border-top: 2.5px solid var(--color-line);
  padding: 8px 0 max(8px, env(safe-area-inset-bottom));
  z-index: 10;
}
@media (min-width: 900px) { .bottom-nav { display: none; } }
.tab {
  flex: 1; background: none; display: flex; flex-direction: column;
  align-items: center; gap: 2px; padding: 6px 0; color: var(--color-ink-soft);
}
.tab.active { color: var(--color-accent); font-weight: 800; }
.icon { font-size: 20px; }
.label { font-size: 10.5px; }
</style>
