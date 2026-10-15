import { createPinia } from 'pinia'
import { createApp } from 'vue'

import { onUnauthorized } from '@/api/http'
import App from '@/App.vue'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'

import '@/styles/tokens.css'
import '@/styles/base.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// 令牌失效时统一清理登录态并回到登录页
onUnauthorized(() => {
  const auth = useAuthStore()
  auth.logout()
  if (router.currentRoute.value.name !== 'login') {
    router.replace({ name: 'login' })
  }
})

app.mount('#app')
