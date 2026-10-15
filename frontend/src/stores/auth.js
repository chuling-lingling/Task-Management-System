import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchMe, login as loginRequest, register as registerRequest } from '@/api/auth'
import { TOKEN_KEY, USER_KEY } from '@/api/http'

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref(readStoredUser())

  const isAuthenticated = computed(() => Boolean(token.value))
  const displayName = computed(() => user.value?.username ?? '')

  function persist(nextToken, nextUser) {
    token.value = nextToken
    user.value = nextUser
    if (nextToken) {
      localStorage.setItem(TOKEN_KEY, nextToken)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
    if (nextUser) {
      localStorage.setItem(USER_KEY, JSON.stringify(nextUser))
    } else {
      localStorage.removeItem(USER_KEY)
    }
  }

  async function login(username, password) {
    const data = await loginRequest({ username, password })
    persist(data.access_token, data.user)
    return data
  }

  async function register(username, password) {
    await registerRequest({ username, password })
    // 注册成功后直接登录，省掉用户再填一次密码
    return login(username, password)
  }

  async function refreshProfile() {
    if (!token.value) return
    try {
      const profile = await fetchMe()
      persist(token.value, profile)
    } catch {
      logout()
    }
  }

  function logout() {
    persist('', null)
  }

  function applyUser(nextUser) {
    if (!nextUser) return
    persist(token.value, nextUser)
  }

  return {
    token,
    user,
    isAuthenticated,
    displayName,
    login,
    register,
    refreshProfile,
    applyUser,
    logout,
  }
})
