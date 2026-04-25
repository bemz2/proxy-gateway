import { ref } from 'vue'

const ACCESS_TOKEN_KEY = 'proxy_gateway_access_token'

const accessToken = ref(localStorage.getItem(ACCESS_TOKEN_KEY))

window.addEventListener('storage', (event) => {
  if (event.key === ACCESS_TOKEN_KEY) {
    accessToken.value = event.newValue
  }
})

export function getAccessToken() {
  return accessToken.value
}

export function useAccessToken() {
  return accessToken
}

export function setAccessToken(token) {
  accessToken.value = token
  localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

export function clearAccessToken() {
  accessToken.value = null
  localStorage.removeItem(ACCESS_TOKEN_KEY)
}
