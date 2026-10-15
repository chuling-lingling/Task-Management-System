<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { createTask, deleteTask, listTasks, setTaskCompletion, updateTask } from '@/api/tasks'
import EmptyState from '@/components/EmptyState.vue'
import TaskFilterTabs from '@/components/TaskFilterTabs.vue'
import TaskForm from '@/components/TaskForm.vue'
import TaskItem from '@/components/TaskItem.vue'
import { isOverdue } from '@/utils/datetime'

const STATUS_OPTIONS = [
  { value: 'open', label: '未完成' },
  { value: 'done', label: '最近 30 天已完成' },
]

const status = ref('open')
const tasks = ref([])
const loading = ref(false)
const submitting = ref(false)
const busyId = ref(null)
const errorMessage = ref('')
const feedback = ref('')

const formMode = ref(null)
const editingTask = ref(null)

let feedbackTimer = null

const overdueCount = computed(
  () => tasks.value.filter((task) => isOverdue(task.planned_at, task.is_completed)).length,
)

const statLabel = computed(() => (status.value === 'open' ? '个未完成任务' : '个已完成任务'))

const emptyTitle = computed(() =>
  status.value === 'open' ? '这里还没有待办' : '最近 30 天没有完成的任务',
)

const emptyDescription = computed(() =>
  status.value === 'open'
    ? '点右上角「新增任务」，从今天的第一件事开始。'
    : '任务标记完成后会在这里保留 30 天，超过后自动隐藏。',
)

function showFeedback(message) {
  feedback.value = message
  if (feedbackTimer) clearTimeout(feedbackTimer)
  feedbackTimer = setTimeout(() => {
    feedback.value = ''
  }, 3000)
}

async function loadTasks() {
  loading.value = true
  errorMessage.value = ''
  try {
    tasks.value = await listTasks(status.value)
  } catch (error) {
    errorMessage.value = error?.message ?? '任务加载失败'
  } finally {
    loading.value = false
  }
}

function openCreate() {
  formMode.value = 'create'
  editingTask.value = null
  errorMessage.value = ''
}

function openEdit(task) {
  formMode.value = 'edit'
  editingTask.value = task
  errorMessage.value = ''
}

function closeForm() {
  formMode.value = null
  editingTask.value = null
}

async function submitForm(payload) {
  submitting.value = true
  errorMessage.value = ''
  try {
    if (formMode.value === 'edit' && editingTask.value) {
      await updateTask(editingTask.value.id, payload)
      showFeedback('任务已更新')
    } else {
      await createTask(payload)
      showFeedback('任务已创建')
    }
    closeForm()
    await loadTasks()
  } catch (error) {
    errorMessage.value = error?.message ?? '保存失败，请重试'
  } finally {
    submitting.value = false
  }
}

async function toggleTask(task) {
  busyId.value = task.id
  errorMessage.value = ''
  try {
    await setTaskCompletion(task.id, !task.is_completed)
    showFeedback(task.is_completed ? '已恢复为未完成' : '已标记完成')
    await loadTasks()
  } catch (error) {
    errorMessage.value = error?.message ?? '操作失败，请重试'
  } finally {
    busyId.value = null
  }
}

async function removeTask(task) {
  busyId.value = task.id
  errorMessage.value = ''
  try {
    await deleteTask(task.id)
    if (editingTask.value?.id === task.id) closeForm()
    showFeedback('任务已删除')
    await loadTasks()
  } catch (error) {
    errorMessage.value = error?.message ?? '删除失败，请重试'
  } finally {
    busyId.value = null
  }
}

watch(status, () => {
  closeForm()
  loadTasks()
})

onMounted(loadTasks)
</script>

<template>
  <main class="tasks">
    <section class="tasks__hero container">
      <div>
        <h1 class="display-lg tasks__headline">今天要做什么？</h1>
        <p class="tasks__lede">
          未完成的任务按计划执行时间排序，先做最该做的；完成的会自动收进归档。
        </p>
      </div>

      <aside class="tasks__stat">
        <p class="tasks__stat-label">{{ statLabel }}</p>
        <p class="display-md tasks__stat-value">{{ tasks.length }}</p>
        <p v-if="status === 'open' && overdueCount > 0" class="tasks__stat-note">
          其中 {{ overdueCount }} 个已超期
        </p>
      </aside>
    </section>

    <section class="container tasks__body">
      <div class="tasks__toolbar">
        <TaskFilterTabs v-model="status" :options="STATUS_OPTIONS" />
        <button v-if="!formMode" type="button" class="btn btn--primary" @click="openCreate">
          新增任务
        </button>
      </div>

      <p v-if="feedback" class="notice notice--success">{{ feedback }}</p>

      <TaskForm
        v-if="formMode"
        :mode="formMode"
        :task="editingTask"
        :submitting="submitting"
        @submit="submitForm"
        @cancel="closeForm"
      />

      <p v-if="errorMessage" class="notice notice--error">{{ errorMessage }}</p>

      <p v-if="loading" class="caption">加载中…</p>

      <template v-else>
        <EmptyState v-if="!tasks.length" :title="emptyTitle" :description="emptyDescription" />
        <ul v-else class="tasks__list">
          <TaskItem
            v-for="task in tasks"
            :key="task.id"
            :task="task"
            :busy="busyId === task.id"
            @toggle="toggleTask"
            @edit="openEdit"
            @delete="removeTask"
          />
        </ul>
      </template>
    </section>
  </main>
</template>

<style scoped>
.tasks {
  padding-bottom: var(--space-section);
}

.tasks__hero {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: end;
  gap: var(--space-xl);
  padding-top: var(--space-xxl);
  padding-bottom: var(--space-xl);
}

.tasks__headline {
  color: var(--color-ink);
}

.tasks__lede {
  margin-top: var(--space-md);
  max-width: 34em;
  font-size: var(--text-body-md);
  color: var(--color-body);
}

.tasks__stat {
  min-width: 196px;
  padding: var(--space-lg);
  border-radius: var(--radius-lg);
  background: var(--color-surface-dark);
  color: var(--color-on-dark);
}

.tasks__stat-label {
  font-size: var(--text-caption);
  color: var(--color-on-dark-soft);
}

.tasks__stat-value {
  margin-top: var(--space-xxs);
  color: var(--color-on-dark);
}

.tasks__stat-note {
  margin-top: var(--space-xs);
  font-size: var(--text-caption);
  color: var(--color-accent-amber);
}

.tasks__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.tasks__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.tasks__list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin: 0;
  padding: 0;
  list-style: none;
}

@media (max-width: 768px) {
  .tasks__hero {
    grid-template-columns: 1fr;
    align-items: start;
  }

  .tasks__stat {
    min-width: 0;
  }

  .tasks__toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .tasks__toolbar .btn {
    width: 100%;
  }
}
</style>
