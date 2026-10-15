<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { updateEmail } from '@/api/auth'

const auth = useAuthStore()
const router = useRouter()

const email = ref(auth.user?.email ?? '')
const submitting = ref(false)
const feedback = ref('')
const errorMessage = ref('')

const avatarInitial = computed(() => {
  const name = (auth.displayName || '').trim()
  return name ? name.charAt(0).toUpperCase() : 'U'
})

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

      <h1 class="display-md settings__title">个人中心</h1>

      <div class="profile">
        <div class="profile__avatar" aria-hidden="true">{{ avatarInitial }}</div>
        <div class="profile__info">
          <div class="profile__name">{{ auth.displayName || '未命名用户' }}</div>
          <div class="profile__meta">用户名 · 任务与提醒仅自己可见</div>
        </div>
      </div>

      <div class="settings__section">
        <h2 class="settings__subtitle">提醒邮箱</h2>
        <p class="settings__lede">
          当任务的「计划执行时间」到达且开启了邮箱提醒，系统会发信到这里。可留空（留空则不发送）。
        </p>

        <form class="settings__form" @submit.prevent="handleSave">
          <div class="field">
            <label class="field__label" for="settings-email">邮箱地址</label>
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
      </div>
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

.profile {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  background: var(--color-surface-soft);
}

.profile__avatar {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: var(--radius-pill);
  background: var(--color-surface-dark);
  color: var(--color-on-dark);
  font-size: var(--text-title-sm);
  font-weight: 600;
}

.profile__info {
  min-width: 0;
}

.profile__name {
  font-size: var(--text-title-sm);
  font-weight: 500;
  color: var(--color-ink);
  word-break: break-all;
}

.profile__meta {
  margin-top: var(--space-xxs);
  font-size: var(--text-caption);
  color: var(--color-muted);
}

.settings__section {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.settings__subtitle {
  font-size: var(--text-title-sm);
  font-weight: 500;
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
</style>
