import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api, imgUrl, formatDate } from '../api.js'

export default {
  setup() {
    const posts = ref([])
    const creating = ref(false)
    const router = useRouter()

    async function load() {
      const res = await api('/posts/feed/all')
      posts.value = await res.json()
    }

    async function createPost() {
      creating.value = true
      try {
        const res = await api('/posts', { method: 'POST', body: JSON.stringify({ caption: '', published: false }) })
        const post = await res.json()
        router.push(`/feed/post/${post.id}`)
      } finally {
        creating.value = false
      }
    }

    async function deletePost(id) {
      if (!confirm('Delete this post?')) return
      await api(`/posts/${id}`, { method: 'DELETE' })
      posts.value = posts.value.filter(p => p.id !== id)
    }

    onMounted(load)

    return { posts, creating, createPost, deletePost, imgUrl, formatDate }
  },
  template: `
    <div>
      <nav-bar />
      <div class="page">
        <div class="feed-header">
          <h1>My Posts</h1>
          <button class="btn btn-primary" @click="createPost" :disabled="creating">
            <span v-if="creating" class="spinner"></span>
            <span v-else>+ New Post</span>
          </button>
        </div>

        <div v-if="posts.length === 0" class="empty-state">No posts yet. Create one!</div>

        <div v-for="post in posts" :key="post.id" class="card post-card">
          <div class="post-card-inner">
            <img v-if="post.images.length" :src="imgUrl(post.images[0].url)" class="post-card-thumb" :alt="post.caption" />
            <div v-else class="post-card-thumb-empty">📷</div>
            <div class="post-card-info">
              <div class="post-card-caption">{{ post.caption || '(no caption)' }}</div>
              <div class="post-card-meta">
                {{ formatDate(post.created_at) }} &middot;
                {{ post.images.length }} image{{ post.images.length !== 1 ? 's' : '' }} &middot;
                <span :style="{color: post.published ? '#2ecc71' : '#e67e22'}">{{ post.published ? 'Published' : 'Draft' }}</span>
              </div>
              <div class="post-card-actions">
                <router-link :to="'/feed/post/' + post.id" class="btn btn-secondary btn-sm">Edit</router-link>
                <button class="btn btn-danger btn-sm" @click="deletePost(post.id)">Delete</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
}
