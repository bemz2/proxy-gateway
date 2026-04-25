<template>
  <AuthPanel title="Вход" subtitle="Используйте email и пароль, указанные при регистрации.">
    <v-alert
      v-if="errorMessage"
      type="error"
      variant="tonal"
      class="mb-4"
    >
      {{ errorMessage }}
    </v-alert>

    <v-form @submit.prevent="submit">
      <v-text-field v-model="form.email" label="Email" type="email" />
      <v-text-field v-model="form.password" label="Пароль" type="password" class="field-gap" />
      <v-btn type="submit" color="primary" block :loading="isLoading" class="field-gap">
        Войти
      </v-btn>
    </v-form>

    <div class="block-gap muted">
      Нет аккаунта?
      <router-link to="/register">Регистрация</router-link>
    </div>
  </AuthPanel>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import AuthPanel from '../components/AuthPanel.vue'
import { api } from '../services/api'
import { setAccessToken } from '../stores/auth'

const router = useRouter()
const isLoading = ref(false)
const errorMessage = ref('')
const form = reactive({
  email: '',
  password: '',
})

async function submit() {
  errorMessage.value = ''

  if (!form.email.trim()) {
    errorMessage.value = 'Введите email'
    return
  }

  if (!form.password) {
    errorMessage.value = 'Введите пароль'
    return
  }

  isLoading.value = true

  try {
    const response = await api.login(form)
    setAccessToken(response.access_token)
    router.push('/profile')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    isLoading.value = false
  }
}
</script>
