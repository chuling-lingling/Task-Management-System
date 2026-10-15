/** 时间展示工具。后端返回的是本地时间字符串（无时区后缀），JS 会按本地时区解析。 */

const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

function startOfDay(date) {
  const copy = new Date(date)
  copy.setHours(0, 0, 0, 0)
  return copy
}

function parse(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatTime(date) {
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function withYear(date) {
  return date.getFullYear() === new Date().getFullYear() ? '' : `${date.getFullYear()}年`
}

/** 计划执行时间的友好描述：今天 09:30 / 明天 09:30 / 10月25日 09:30 */
export function describePlannedAt(value) {
  const date = parse(value)
  if (!date) return null

  const diffDays = Math.round((startOfDay(date) - startOfDay(new Date())) / 86400000)
  const time = formatTime(date)

  if (diffDays === 0) return `今天 ${time}`
  if (diffDays === 1) return `明天 ${time}`
  if (diffDays === -1) return `昨天 ${time}`
  if (diffDays > 1 && diffDays <= 6) return `${WEEKDAYS[date.getDay()]} ${time}`
  return `${withYear(date)}${date.getMonth() + 1}月${date.getDate()}日 ${time}`
}

/** 完成时间的展示：今天 09:30 / 10月25日 09:30 */
export function formatCompletedAt(value) {
  const date = parse(value)
  if (!date) return null
  return `${withYear(date)}${date.getMonth() + 1}月${date.getDate()}日 ${formatTime(date)}`
}

export function formatCreatedAt(value) {
  const date = parse(value)
  if (!date) return null
  return `${withYear(date)}${date.getMonth() + 1}月${date.getDate()}日创建`
}

/** 计划时间已过且任务未完成 */
export function isOverdue(plannedAt, isCompleted) {
  const date = parse(plannedAt)
  if (!date || isCompleted) return false
  return date.getTime() < Date.now()
}

/** Date → <input type="datetime-local"> 需要的 YYYY-MM-DDTHH:mm */
export function toDateTimeLocalValue(value) {
  const date = parse(value)
  if (!date) return ''
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

/** <input type="datetime-local"> 的值 → 后端接受的 ISO 字符串 */
export function fromDateTimeLocalValue(value) {
  if (!value) return null
  return value.length === 16 ? `${value}:00` : value
}
