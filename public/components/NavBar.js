import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { isLoggedIn, clearToken } from '../api.js'

export default {
  setup() {
    const router = useRouter()
    const loggedIn = computed(isLoggedIn)
    function logout() { clearToken(); router.push('/') }
    return { loggedIn, logout }
  },
  template: `
    <nav>
      <div class="inner">
        <router-link class="brand" to="/">Blog</router-link>
        <div class="nav-links">
          <router-link to="/">Home</router-link>
          <template v-if="loggedIn">
            <router-link to="/feed">Feed</router-link>
            <router-link to="/feed/profile">Profile</router-link>
            <button @click="logout">Log out</button>
          </template>
          <template v-else>
            <router-link to="/login">Log in</router-link>
          </template>
        </div>
      </div>
    </nav>
  `
}
