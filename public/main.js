import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn } from './api.js'
import NavBar from './components/NavBar.js'
import PublicProfileView from './pages/PublicProfileView.js'
import LoginView from './pages/LoginView.js'
import FeedView from './pages/FeedView.js'
import EditPostView from './pages/EditPostView.js'
import EditProfileView from './pages/EditProfileView.js'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/',                  component: PublicProfileView },
    { path: '/login',             component: LoginView },
    { path: '/feed',              component: FeedView,         meta: { requiresAuth: true } },
    { path: '/feed/post/:id',     component: EditPostView,     meta: { requiresAuth: true } },
    { path: '/feed/profile',      component: EditProfileView,  meta: { requiresAuth: true } },
  ]
})

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !isLoggedIn()) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.path === '/login' && isLoggedIn()) {
    return '/feed'
  }
})

const app = createApp({ template: `<router-view />` })
app.component('nav-bar', NavBar)
app.use(router)
app.mount('#app')
