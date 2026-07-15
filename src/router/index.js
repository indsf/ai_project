import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import BoardListView from '../views/BoardListView.vue'
import BoardWriteView from '../views/BoardWriteView.vue'
import BoardDetailView from '../views/BoardDetailView.vue'
import FestivalListView from '../views/FestivalListView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/board', name: 'board-list', component: BoardListView },
  { path: '/board/write', name: 'board-write', component: BoardWriteView },
  { path: '/board/:id', name: 'board-detail', component: BoardDetailView, props: true },
  { path: '/festivals', name: 'festivals', component: FestivalListView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
