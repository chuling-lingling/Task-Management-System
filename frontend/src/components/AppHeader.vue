<script setup>
import { useRouter } from 'vue-router'

import BrandMark from '@/components/BrandMark.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.replace({ name: 'login' })
}
</script>

<template>
  <header class="nav">
    <div class="nav__inner container">
      <div class="nav__brand">
        <BrandMark />
        <span class="nav__wordmark">任务管理</span>
      </div>
      <div class="nav__actions">
        <RouterLink to="/settings" class="nav__user" title="点击进入设置">{{ auth.displayName }}</RouterLink>
        <button type="button" class="btn btn--secondary nav__logout" @click="handleLogout">退出登录</button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.nav {
  position: sticky;
  top: 0;
  z-index: 10;
  height: var(--nav-height);
  background: var(--color-canvas);
  border-bottom: 1px solid var(--color-hairline);
}

.nav__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

.nav__brand {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  color: var(--color-ink);
}

.nav__wordmark {
  font-size: var(--text-title-sm);
  font-weight: 500;
}

.nav__actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.nav__user {
  font-size: var(--text-body-sm);
  color: var(--color-muted);
  text-decoration: none;
  transition: color 0.15s ease;
}

.nav__user:hover {
  color: var(--color-ink);
}

.nav__logout {
  height: 36px;
  padding: 0 16px;
}

@media (max-width: 640px) {
  .nav__user {
    display: none;
  }
}
</style>
