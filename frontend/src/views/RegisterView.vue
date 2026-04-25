<template>
  <AuthPanel title="Регистрация" subtitle="После регистрации ключ активации будет отправлен через backend worker.">
    <v-alert
      v-if="successMessage"
      type="success"
      variant="tonal"
      class="mb-4"
    >
      {{ successMessage }}
    </v-alert>

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
      <v-text-field
        v-model="form.password_confirmation"
        label="Подтверждение пароля"
        type="password"
        class="field-gap"
      />
      <v-btn type="submit" color="primary" block :loading="isLoading" class="field-gap">
        Зарегистрироваться
      </v-btn>
    </v-form>

    <div class="block-gap muted">
      Уже есть аккаунт?
      <router-link to="/login">Войти</router-link>
    </div>
  </AuthPanel>
</template>

<script setup>
import { reactive, ref } from 'vue'

import AuthPanel from '../components/AuthPanel.vue'
import { api } from '../services/api'

const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const form = reactive({
  email: '',
  password: '',
  password_confirmation: '',
})

async function submit() {
  errorMessage.value = ''
  successMessage.value = ''

  if (!form.email.trim()) {
    errorMessage.value = 'Введите email'
    return
  }

  if (form.password.length < 8) {
    errorMessage.value = 'Пароль должен быть не короче 8 символов'
    return
  }

  if (form.password !== form.password_confirmation) {
    errorMessage.value = 'Пароли не совпадают'
    return
  }

  isLoading.value = true

  try {
    await api.register(form)
    successMessage.value = 'Письмо с ключом отправлено на почту'
    form.email = ''
    form.password = ''
    form.password_confirmation = ''
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    isLoading.value = false
  }
}
</script>
