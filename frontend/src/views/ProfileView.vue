<template>
  <div class="page-wrap">
    <div class="profile-grid">
      <div class="panel">
        <div class="panel-header">
          <div class="title">Личный кабинет</div>
          <div class="subtitle">Текущий ключ, обновление ключа и смена пароля.</div>
        </div>
        <div class="panel-body">
          <v-alert
            v-if="message.text"
            :type="message.type"
            variant="tonal"
            class="mb-4"
          >
            {{ message.text }}
          </v-alert>

          <div class="info-row">
            <div class="section-title">Пользователь</div>
            <div>{{ profile.email }}</div>
          </div>

          <div class="info-row block-gap">
            <div class="section-title">Ключ активации</div>
            <div v-if="profile.activation_key" class="mono">
              {{ profile.activation_key }}
            </div>
            <div v-else class="muted">
              Ключ уже использован или еще не сгенерирован.
            </div>
          </div>

          <div class="actions-row block-gap">
            <v-btn color="primary" :loading="isRefreshingKey" @click="refreshKey">
              Обновить ключ
            </v-btn>
            <v-btn variant="outlined" @click="loadProfile">
              Обновить профиль
            </v-btn>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="title">Смена пароля</div>
        </div>
        <div class="panel-body">
          <v-form @submit.prevent="changePassword">
            <v-text-field v-model="passwordForm.current_password" label="Текущий пароль" type="password" />
            <v-text-field v-model="passwordForm.new_password" label="Новый пароль" type="password" class="field-gap" />
            <v-text-field
              v-model="passwordForm.new_password_confirmation"
              label="Подтверждение нового пароля"
              type="password"
              class="field-gap"
            />
            <v-btn type="submit" color="primary" :loading="isChangingPassword" class="field-gap">
              Сменить пароль
            </v-btn>
          </v-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api } from '../services/api'
import { clearAccessToken } from '../stores/auth'

const router = useRouter()
const isRefreshingKey = ref(false)
const isChangingPassword = ref(false)
const profile = reactive({
  email: '',
  activation_key: null,
})
const passwordForm = reactive({
  current_password: '',
  new_password: '',
  new_password_confirmation: '',
})
const message = reactive({
  type: 'success',
  text: '',
})

function setMessage(type, text) {
  message.type = type
  message.text = text
}

async function loadProfile() {
  try {
    const response = await api.getProfile()
    profile.email = response.email
    profile.activation_key = response.activation_key
  } catch (error) {
    clearAccessToken()
    router.push('/login')
  }
}

async function refreshKey() {
  setMessage('success', '')
  isRefreshingKey.value = true

  try {
    const response = await api.refreshKey()
    profile.activation_key = response.activation_key
    setMessage('success', 'Новый ключ сгенерирован и отправлен.')
  } catch (error) {
    setMessage('error', error.message)
  } finally {
    isRefreshingKey.value = false
  }
}

async function changePassword() {
  setMessage('success', '')

  if (passwordForm.new_password.length < 8) {
    setMessage('error', 'Новый пароль должен быть не короче 8 символов')
    return
  }

  if (passwordForm.new_password !== passwordForm.new_password_confirmation) {
    setMessage('error', 'Новые пароли не совпадают')
    return
  }

  isChangingPassword.value = true

  try {
    await api.changePassword(passwordForm)
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    passwordForm.new_password_confirmation = ''
    setMessage('success', 'Пароль обновлен.')
  } catch (error) {
    setMessage('error', error.message)
  } finally {
    isChangingPassword.value = false
  }
}

onMounted(loadProfile)
</script>
