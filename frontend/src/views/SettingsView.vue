<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { updateEmail } from '@/api/auth'

const auth = useAuthStore()
const router = useRouter()

const email = ref(auth.user?.email ?? '')
const submitting = ref(false)
const feedback = ref('')
const errorMessage = ref('')

async function handleSave() {
  errorMessage.value = ''
  feedback.value = ''
  const trimmed = email.value.trim()
  if (trimmed && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(trimmed)) {
    errorMessage.value = '邮箱格式不正确'
    return
  }

  submitting.value = true
  try {
    const updated = await updateEmail(trimmed || null)
    auth.applyUser(updated)
    feedback.value = '邮箱已保存'
    email.value = updated.email ?? ''
  } catch (error) {
    errorMessage.value = error?.message ?? '保存失败，请重试'
  } finally {
    submitting.value = false
  }
}

function goBack() {
  router.push({ name: 'tasks' })
}
</script>

<template>
  <main class="settings">
    <section class="container settings__panel card">
      <button type="button" class="settings__back" @click="goBack">← 返回任务</button>

      <h1 class="display-md settings__title">账户设置</h1>
      <p class="settings__lede">
        设置用于接收任务提醒的邮箱。当任务的「计划执行时间」到达且开启了邮箱提醒，系统会发信到这里。
      </p>

      <form class="settings__form" @submit.prevent="handleSave">
        <div class="field">
          <label class="field__label" for="settings-email">提醒邮箱（可留空）</label>
          <input
            id="settings-email"
            v-model="email"
            class="input"
            type="email"
            autocomplete="email"
            placeholder="例如 you@example.com"
          />
          <span class="field__hint">发信由系统从你配置的发件域名统一发出，这里填你用来收信的地址。</span>
        </div>

        <p v-if="feedback" class="notice notice--success">{{ feedback }}</p>
        <p v-if="errorMessage" class="notice notice--error">{{ errorMessage }}</p>

        <div class="settings__actions">
          <button type="submit" class="btn btn--primary" :disabled="submitting">
            {{ submitting ? '保存中…' : '保存邮箱' }}
          </button>
        </div>
      </form>

      <p class="settings__account">
        当前登录用户：<strong>{{ auth.displayName }}</strong>
      </p>
    </section>
  </main>
</template>

<style scoped>
.settings {
  padding: var(--space-section) 0;
}

.settings__panel {
  max-width: 560px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.settings__back {
  align-self: flex-start;
  background: none;
  border: none;
  padding: 0;
  font-size: var(--text-body-sm);
  color: var(--color-muted);
  cursor: pointer;
}

.settings__back:hover {
  color: var(--color-ink);
}

.settings__title {
  color: var(--color-ink);
}

.settings__lede {
  font-size: var(--text-body-md);
  color: var(--color-body);
  line-height: 1.7;
}

.settings__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.settings__actions {
  margin-top: var(--space-xs);
}

.settings__account {
  font-size: var(--text-body-sm);
  color: var(--color-muted);
  border-top: 1px solid var(--color-hairline);
  padding-top: var(--space-md);
}
</style>
