import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { setToken } from '../api.js'

export default {
  setup() {
    const passphrase = ref('')
    const error = ref('')
    const loading = ref(false)
    const router = useRouter()
    const route = useRoute()

    async function submit() {
      error.value = ''
      loading.value = true
      try {
        const res = await fetch('/api/auth/token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ passphrase: passphrase.value })
        })
        if (!res.ok) { error.value = 'Wrong passphrase.'; return }
        const data = await res.json()
        setToken(data.access_token)
        router.push(route.query.redirect || '/feed')
      } catch (e) {
        error.value = 'Network error.'
      } finally {
        loading.value = false
      }
    }

    return { passphrase, error, loading, submit }
  },
  template: `
    <div>
      <nav-bar />
      <div class="login-wrap">
        <div class="card">
          <h1>Sign in</h1>
          <form @submit.prevent="submit">
            <div class="form-group">
              <label>Passphrase</label>
              <input type="password" v-model="passphrase" autofocus placeholder="Enter passphrase" />
            </div>
            <div class="error-msg" v-if="error">{{ error }}</div>
            <button type="submit" class="btn btn-primary" style="width:100%; justify-content:center;" :disabled="loading">
              <span v-if="loading" class="spinner"></span>
              <span v-else>Sign in</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  `
}
