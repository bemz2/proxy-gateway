<template>
  <v-app>
    <div class="app-shell">
      <header class="topbar">
        <div class="topbar-inner">
          <div class="topbar-title">Proxy Gateway</div>
          <div class="topbar-actions">
            <v-btn
              v-if="isAuthenticated"
              variant="text"
              size="small"
              @click="logout"
            >
              Выйти
            </v-btn>
          </div>
        </div>
      </header>
      <router-view />
    </div>
  </v-app>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { clearAccessToken, getAccessToken } from './stores/auth'

const route = useRoute()
const router = useRouter()
const isAuthenticated = computed(() => {
  route.fullPath
  return Boolean(getAccessToken())
})

function logout() {
  clearAccessToken()
  router.push('/login')
}
</script>
