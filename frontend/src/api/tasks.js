import http from './http'

export function listTasks(status = 'open') {
  return http.get('/tasks', { params: { status } })
}

export function createTask(payload) {
  return http.post('/tasks', payload)
}

export function updateTask(taskId, payload) {
  return http.patch(`/tasks/${taskId}`, payload)
}

export function deleteTask(taskId) {
  return http.delete(`/tasks/${taskId}`)
}

export function setTaskCompletion(taskId, completed) {
  return http.patch(`/tasks/${taskId}/completion`, { completed })
}
