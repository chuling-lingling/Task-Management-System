<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import BrandMark from '@/components/BrandMark.vue'
import { useAuthStore } from '@/stores/auth'

const USERNAME_PATTERN = /^[A-Za-z0-9_]+$/

const auth = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const errorMessage = ref('')
const submitting = ref(false)

function validate() {
  const name = username.value.trim()
  if (!USERNAME_PATTERN.test(name) || name.length < 3 || name.length > 32) {
    return '用户名需为 3-32 位字母、数字或下划线'
  }
  if (password.value.length < 8 || password.value.length > 64) {
    return '密码长度需为 8-64 位'
  }
  if (password.value !== confirmPassword.value) {
    return '两次输入的密码不一致'
  }
  return ''
}

async function handleSubmit() {
  errorMessage.value = validate()
  if (errorMessage.value) return

  submitting.value = true
  try {
    await auth.register(username.value.trim(), password.value)
    router.replace('/')
  } catch (error) {
    errorMessage.value = error?.message ?? '注册失败，请重试'
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
        <h1 class="display-lg auth__headline">从今天要做的第一件事开始。</h1>
        <p class="auth__lede">
          注册只需要一个用户名和密码。账号之间数据完全隔离，你的任务只有你能看到和修改。
        </p>
        <ul class="auth__points">
          <li>用户名 3-32 位，仅字母、数字、下划线</li>
          <li>密码 8-64 位，以 Argon2id 哈希存储</li>
          <li>注册成功后直接进入任务界面</li>
        </ul>
      </section>

      <section class="auth__panel card">
        <h2 class="display-sm">注册</h2>
        <p class="auth__switch">
          已经有账号了？<RouterLink to="/login">去登录</RouterLink>
        </p>

        <form class="auth__form" @submit.prevent="handleSubmit">
          <div class="field">
            <label class="field__label" for="register-username">用户名</label>
            <input
              id="register-username"
              v-model="username"
              class="input"
              type="text"
              autocomplete="username"
              maxlength="32"
              placeholder="3-32 位字母、数字或下划线"
            />
          </div>

          <div class="field">
            <label class="field__label" for="register-password">密码</label>
            <input
              id="register-password"
              v-model="password"
              class="input"
              type="password"
              autocomplete="new-password"
              maxlength="64"
              placeholder="至少 8 位"
            />
          </div>

          <div class="field">
            <label class="field__label" for="register-confirm">确认密码</label>
            <input
              id="register-confirm"
              v-model="confirmPassword"
              class="input"
              type="password"
              autocomplete="new-password"
              maxlength="64"
              placeholder="再输入一次"
            />
          </div>

          <p v-if="errorMessage" class="notice notice--error">{{ errorMessage }}</p>

          <button type="submit" class="btn btn--primary btn--block" :disabled="submitting">
            {{ submitting ? '注册中…' : '注册并登录' }}
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
  max-width: 13em;
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
