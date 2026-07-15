<script setup>
import BottomNav from './components/BottomNav.vue'
import ChatWidget from './components/ChatWidget.vue'
</script>

<template>
  <header class="site-header">
    <div class="nav">
      <router-link to="/" class="logo">오늘, 구미<span class="dot">.</span></router-link>
      <ul class="nav-links">
        <li><router-link to="/">홈</router-link></li>
        <li><router-link to="/festivals">축제·관광</router-link></li>
        <li><router-link to="/board">커뮤니티</router-link></li>
      </ul>
      <router-link class="nav-cta" to="/board/write">글쓰기 ✏️</router-link>
    </div>
  </header>
  <main>
    <router-view />
  </main>
  <BottomNav />
  <ChatWidget />
</template>

<style scoped>
.site-header {
  position: sticky;
  top: 0;
  z-index: 60;
  background: rgba(255, 253, 249, 0.92);
  backdrop-filter: blur(8px);
  border-bottom: 2.5px solid var(--color-line);
}
.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
}
.logo {
  font-family: var(--font-display);
  font-size: 20px;
}
.logo .dot { color: var(--color-accent); }
.nav-links {
  display: none;
  gap: 22px;
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: 14px;
  font-weight: 700;
}
.nav-cta {
  font-size: 12px;
  font-weight: 800;
  background: var(--color-ink);
  color: #fff;
  padding: 8px 14px;
  border-radius: 999px;
  border: 2px solid var(--color-line);
}
@media (min-width: 900px) {
  .nav-links { display: flex; }
}
</style>
