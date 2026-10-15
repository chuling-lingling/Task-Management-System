<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import BrandMark from '@/components/BrandMark.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const errorMessage = ref('')
const submitting = ref(false)

async function handleSubmit() {
  errorMessage.value = ''
  if (!username.value.trim() || !password.value) {
    errorMessage.value = '请填写用户名和密码'
    return
  }

  submitting.value = true
  try {
    await auth.login(username.value.trim(), password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    router.replace(redirect)
  } catch (error) {
    errorMessage.value = error?.message ?? '登录失败，请重试'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="auth">
    <div class="auth__grid container">
      <section class="auth__intro">
        <div class="auth__wordmark">
          <BrandMark />
          <span>任务管理</span>
        </div>
        <h1 class="display-lg auth__headline">把要做的事，按计划放好。</h1>
        <p class="auth__lede">
          创建任务、设定计划执行时间、标记完成。未完成的排在前面，已完成的保留最近 30 天。
        </p>
        <ul class="auth__points">
          <li>计划执行时间决定列表顺序</li>
          <li>完成与恢复可随时切换</li>
          <li>每个人只看得到自己的任务</li>
        </ul>
      </section>

      <section class="auth__panel card">
        <h2 class="display-sm">登录</h2>
        <p class="auth__switch">
          还没有账号？<RouterLink to="/register">立即注册</RouterLink>
        </p>

        <form class="auth__form" @submit.prevent="handleSubmit">
          <div class="field">
            <label class="field__label" for="login-username">用户名</label>
            <input
              id="login-username"
              v-model="username"
              class="input"
              type="text"
              autocomplete="username"
              placeholder="你的用户名"
            />
          </div>

          <div class="field">
            <label class="field__label" for="login-password">密码</label>
            <input
              id="login-password"
              v-model="password"
              class="input"
              type="password"
              autocomplete="current-password"
              placeholder="你的密码"
            />
          </div>

          <p v-if="errorMessage" class="notice notice--error">{{ errorMessage }}</p>

          <button type="submit" class="btn btn--primary btn--block" :disabled="submitting">
            {{ submitting ? '登录中…' : '登录' }}
          </button>
        </form>
      </section>
    </div>
  </main>
</template>

<style scoped>
.auth {
  padding: var(--space-section) 0;
}

.auth__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-xxl);
  align-items: center;
}

.auth__wordmark {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  color: var(--color-ink);
  font-size: var(--text-title-sm);
  font-weight: 500;
  margin-bottom: var(--space-lg);
}

.auth__headline {
  color: var(--color-ink);
  max-width: 12em;
}

.auth__lede {
  margin-top: var(--space-lg);
  max-width: 30em;
  font-size: var(--text-body-md);
  color: var(--color-body);
}

.auth__points {
  margin: var(--space-lg) 0 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.auth__points li {
  font-size: var(--text-body-sm);
  color: var(--color-muted);
  padding-left: var(--space-md);
  position: relative;
}

.auth__points li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.6em;
  width: 6px;
  height: 6px;
  border-radius: var(--radius-pill);
  background: var(--color-primary);
}

.auth__panel {
  max-width: 420px;
  justify-self: end;
  width: 100%;
}

.auth__switch {
  margin-top: var(--space-xs);
  font-size: var(--text-body-sm);
  color: var(--color-muted);
}

.auth__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-top: var(--space-lg);
}

@media (max-width: 900px) {
  .auth__grid {
    grid-template-columns: 1fr;
    gap: var(--space-xl);
  }

  .auth__panel {
    justify-self: stretch;
    max-width: none;
  }
}
</style>
