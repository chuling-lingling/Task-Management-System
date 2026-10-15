<script setup>
import { computed, ref, watch } from 'vue'

import { fromDateTimeLocalValue, toDateTimeLocalValue } from '@/utils/datetime'

const props = defineProps({
  mode: { type: String, default: 'create' },
  task: { type: Object, default: null },
  submitting: { type: Boolean, default: false },
})

const emit = defineEmits(['submit', 'cancel'])

const title = ref('')
const description = ref('')
const plannedAt = ref('')
const emailReminder = ref(false)
const emailReminderMode = ref('once')
const localError = ref('')

watch(
  () => props.task,
  (task) => {
    title.value = task?.title ?? ''
    description.value = task?.description ?? ''
    plannedAt.value = toDateTimeLocalValue(task?.planned_at)
    emailReminder.value = task?.email_reminder_enabled ?? false
    emailReminderMode.value = task?.email_reminder_mode ?? 'once'
    localError.value = ''
  },
  { immediate: true },
)

const heading = computed(() => (props.mode === 'edit' ? '编辑任务' : '新增任务'))

function handleSubmit() {
  const trimmedTitle = title.value.trim()
  if (!trimmedTitle) {
    localError.value = '请填写任务标题'
    return
  }
  localError.value = ''
  emit('submit', {
    title: trimmedTitle,
    description: description.value.trim() || null,
    planned_at: fromDateTimeLocalValue(plannedAt.value),
    email_reminder_enabled: emailReminder.value,
    email_reminder_mode: emailReminder.value ? emailReminderMode.value : 'once',
  })
}
</script>

<template>
  <form class="form card" @submit.prevent="handleSubmit">
    <h2 class="display-sm form__heading">{{ heading }}</h2>

    <div class="form__grid">
      <div class="field">
        <label class="field__label" for="task-title">任务标题</label>
        <input
          id="task-title"
          v-model="title"
          class="input"
          type="text"
          maxlength="200"
          placeholder="例如：写季度总结"
          autocomplete="off"
        />
      </div>

      <div class="field">
        <label class="field__label" for="task-planned-at">计划执行时间（可留空）</label>
        <input id="task-planned-at" v-model="plannedAt" class="input" type="datetime-local" />
        <span class="field__hint">用于排序展示，与创建时间、完成时间是三个独立概念</span>
        <label class="checkbox">
          <input id="task-email-reminder" v-model="emailReminder" type="checkbox" />
          <span>启用邮箱提醒（到达计划时间发邮件到我的收件邮箱）</span>
        </label>
        <div v-if="emailReminder" class="field__sub">
          <span class="field__label">提醒频率</span>
          <label class="radio">
            <input type="radio" value="once" v-model="emailReminderMode" />
            <span>只发一次（默认）</span>
          </label>
          <label class="radio">
            <input type="radio" value="hourly" v-model="emailReminderMode" />
            <span>每小时发一次</span>
          </label>
          <label class="radio">
            <input type="radio" value="daily" v-model="emailReminderMode" />
            <span>每天发一次（持续提醒直到完成）</span>
          </label>
        </div>
      </div>

      <div class="field form__full">
        <label class="field__label" for="task-description">任务描述（可留空）</label>
        <textarea
          id="task-description"
          v-model="description"
          class="textarea"
          maxlength="2000"
          placeholder="补充背景、验收标准等"
        />
      </div>
    </div>

    <p v-if="localError" class="field__error">{{ localError }}</p>

    <div class="form__actions">
      <button type="submit" class="btn btn--primary" :disabled="submitting">
        {{ submitting ? '保存中…' : '保存任务' }}
      </button>
      <button type="button" class="btn btn--secondary" :disabled="submitting" @click="emit('cancel')">
        取消
      </button>
    </div>
  </form>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.form__heading {
  color: var(--color-ink);
}

.form__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md) var(--space-lg);
}

.form__full {
  grid-column: 1 / -1;
}

.form__actions {
  display: flex;
  gap: var(--space-sm);
}

.checkbox {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  margin-top: var(--space-sm);
  font-size: var(--text-body-sm);
  color: var(--color-body);
  cursor: pointer;
}

.checkbox input {
  width: 16px;
  height: 16px;
  accent-color: var(--color-primary);
}

.field__sub {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  margin-top: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  background: var(--color-surface-soft);
}

.field__sub .field__label {
  margin-bottom: var(--space-xxs);
}

.radio {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--text-body-sm);
  color: var(--color-body);
  cursor: pointer;
}

.radio input {
  width: 16px;
  height: 16px;
  accent-color: var(--color-primary);
}

@media (max-width: 768px) {
  .form__grid {
    grid-template-columns: 1fr;
  }
}
</style>
