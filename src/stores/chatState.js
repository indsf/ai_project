import { reactive } from 'vue'

export const chatState = reactive({
  messages: [
    { role: 'assistant', content: '안녕하세요! 구미 지역 축제, 관광지, 맛집이 궁금하면 물어보세요.' },
  ],
})