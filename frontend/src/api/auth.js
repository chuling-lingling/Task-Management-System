import http from './http'

export function register(payload) {
  return http.post('/auth/register', payload)
}

export function login(payload) {
  return http.post('/auth/login', payload)
}

export function fetchMe() {
  return http.get('/auth/me')
}

export function updateEmail(email) {
  return http.patch('/auth/me', { email })
}
