<script setup>
import { computed, ref } from 'vue'

import { describePlannedAt, formatCompletedAt, isOverdue } from '@/utils/datetime'

const props = defineProps({
  task: { type: Object, required: true },
  busy: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle', 'edit', 'delete'])

const confirmingDelete = ref(false)

const plannedLabel = computed(() => describePlannedAt(props.task.planned_at))
const completedLabel = computed(() => formatCompletedAt(props.task.completed_at))
const overdue = computed(() => isOverdue(props.task.planned_at, props.task.is_completed))

const REMINDER_MODE_LABELS = {
  once: '只发一次',
  hourly: '每小时',
  daily: '每天',
}

const reminderLabel = computed(() => {
  if (!props.task.email_reminder_enabled) return ''
  return REMINDER_MODE_LABELS[props.task.email_reminder_mode] || '提醒'
})
</script>

<template>
  <li class="task" :class="{ 'task--done': task.is_completed }">
    <button
      type="button"
      class="task__check"
      :class="{ 'task__check--done': task.is_completed }"
      :aria-label="task.is_completed ? '恢复为未完成' : '标记为已完成'"
      :disabled="busy"
      @click="emit('toggle', task)"
    >
      <svg v-if="task.is_completed" viewBox="0 0 16 16" aria-hidden="true">
        <path
          d="M3.5 8.5l3 3 6-7"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </button>

    <div class="task__main">
      <div class="task__head">
        <h3 class="task__title">{{ task.title }}</h3>
        <span v-if="overdue" class="badge badge--error">已超期</span>
      </div>

      <p v-if="task.description" class="task__description">{{ task.description }}</p>

      <div class="task__meta">
        <span
          v-if="plannedLabel"
          class="task__meta-item"
          :class="{ 'task__meta-item--overdue': overdue }"
        >
          计划 {{ plannedLabel }}
        </span>
        <span v-if="completedLabel" class="task__meta-item">完成于 {{ completedLabel }}</span>
        <span
          v-if="reminderLabel"
          class="task__meta-item task__meta-item--reminder"
        >邮件提醒·{{ reminderLabel }}</span>
        <span v-if="!plannedLabel && !completedLabel" class="task__meta-item task__meta-item--soft">
          未设计划时间
        </span>
      </div>
    </div>

    <div class="task__actions">
      <template v-if="confirmingDelete">
        <button type="button" class="btn btn--text task__action--danger" @click="emit('delete', task)">
          确认删除
        </button>
        <button type="button" class="btn btn--text" @click="confirmingDelete = false">取消</button>
      </template>
      <template v-else>
        <button type="button" class="btn btn--text" @click="emit('edit', task)">编辑</button>
        <button
          type="button"
          class="btn btn--text task__action--danger"
          @click="confirmingDelete = true"
        >
          删除
        </button>
      </template>
    </div>
  </li>
</template>

<style scoped>
.task {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

.task--done {
  background: var(--color-surface-soft);
}

.task__check {
  flex: none;
  width: 22px;
  height: 22px;
  margin-top: 2px;
  padding: 0;
  border: 1.5px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  background: var(--color-canvas);
  color: var(--color-on-dark);
  cursor: pointer;
}

.task__check:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.task__check--done {
  display: flex;
  align-items: center;
  justify-content: center;
  border-color: var(--color-surface-dark);
  background: var(--color-surface-dark);
}

.task__check svg {
  width: 14px;
  height: 14px;
}

.task__main {
  flex: 1;
  min-width: 0;
}

.task__head {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.task__title {
  font-size: var(--text-title-sm);
  font-weight: 500;
  line-height: 1.4;
  color: var(--color-ink);
  word-break: break-word;
}

.task--done .task__title {
  color: var(--color-muted);
  text-decoration: line-through;
}

.task__description {
  margin-top: var(--space-xxs);
  font-size: var(--text-body-sm);
  color: var(--color-body);
  white-space: pre-wrap;
  word-break: break-word;
}

.task--done .task__description {
  color: var(--color-muted-soft);
}

.task__meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: var(--space-xs);
}

.task__meta-item {
  font-family: var(--font-mono);
  font-size: var(--text-caption);
  color: var(--color-muted);
}

.task__meta-item--soft {
  font-family: var(--font-sans);
  color: var(--color-muted-soft);
}

.task__meta-item--overdue {
  color: var(--color-error);
}

.task__meta-item--reminder {
  color: var(--color-primary);
}

.task__actions {
  flex: none;
  display: flex;
  gap: var(--space-sm);
  font-size: var(--text-body-sm);
}

.task__action--danger {
  color: var(--color-error);
}

@media (max-width: 640px) {
  .task {
    flex-wrap: wrap;
    padding: var(--space-md);
  }

  .task__actions {
    width: 100%;
    padding-left: 38px;
  }
}
</style>
