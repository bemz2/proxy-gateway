import { createApp } from 'vue'
import { createVuetify } from 'vuetify'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'

import App from './App.vue'
import router from './router'
import './styles.css'

const vuetify = createVuetify({
  defaults: {
    VBtn: {
      rounded: '0',
      elevation: 0,
    },
    VCard: {
      rounded: '0',
      elevation: 0,
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
      rounded: '0',
    },
    VAlert: {
      rounded: '0',
    },
  },
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        dark: false,
        colors: {
          primary: '#1f1f1f',
          secondary: '#5f5f5f',
          surface: '#ffffff',
          background: '#f4f4f4',
          error: '#b3261e',
          success: '#1b5e20',
        },
      },
    },
  },
})

createApp(App).use(router).use(vuetify).mount('#app')
