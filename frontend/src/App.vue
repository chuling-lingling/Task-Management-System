<script setup>
import { onMounted } from 'vue'
import { RouterView, useRoute } from 'vue-router'

import AppHeader from '@/components/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()

onMounted(() => {
  // 刷新页面后用令牌换一次最新的用户信息，令牌失效会被拦截器兜住
  if (auth.isAuthenticated) {
    auth.refreshProfile()
  }
})
</script>

<template>
  <AppHeader v-if="route.meta.requiresAuth" />
  <RouterView />
</template>
