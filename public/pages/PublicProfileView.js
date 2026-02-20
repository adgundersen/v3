import { ref, onMounted, onUnmounted } from 'vue'
import { api, imgUrl, formatDate } from '../api.js'

export default {
  setup() {
    const profile = ref(null)
    const posts = ref([])
    const activePost = ref(null)
    const carouselIndex = ref(0)
    const filterTag = ref(null)

    console.log("PUBLIC")

    async function load() {
      const [pRes, postsRes] = await Promise.all([
        api('/profile'),
        api('/posts' + (filterTag.value ? `?tag=${encodeURIComponent(filterTag.value)}` : ''))
      ])
      profile.value = await pRes.json()
      posts.value = await postsRes.json()
    }

    function openPost(post) { activePost.value = post; carouselIndex.value = 0 }
    function closePost() { activePost.value = null }

    function prevImage() {
      if (!activePost.value) return
      const len = activePost.value.images.length
      carouselIndex.value = (carouselIndex.value - 1 + len) % len
    }

    function nextImage() {
      if (!activePost.value) return
      const len = activePost.value.images.length
      carouselIndex.value = (carouselIndex.value + 1) % len
    }

    function filterByTag(name) { filterTag.value = name; load() }
    function clearFilter() { filterTag.value = null; load() }

    function handleKey(e) {
      if (!activePost.value) return
      if (e.key === 'ArrowLeft') prevImage()
      if (e.key === 'ArrowRight') nextImage()
      if (e.key === 'Escape') closePost()
    }

    onMounted(() => { load(); document.addEventListener('keydown', handleKey) })
    onUnmounted(() => { document.removeEventListener('keydown', handleKey) })

    return { profile, posts, activePost, carouselIndex, filterTag, openPost, closePost, prevImage, nextImage, filterByTag, clearFilter, imgUrl, formatDate }
  },
  template: `
    <div>
      <nav-bar />
      <div class="page" v-if="profile">
        <div class="profile-header">
          <img v-if="profile.avatar_url" :src="imgUrl(profile.avatar_url)" class="profile-avatar" alt="Avatar" />
          <div v-else class="profile-avatar-placeholder">👤</div>
          <div class="profile-info">
            <h1>{{ profile.name || 'No name set' }}</h1>
            <div class="profile-bio">{{ profile.bio }}</div>
            <div class="profile-links">
              <a v-for="link in profile.links" :key="link.url" :href="link.url" target="_blank" rel="noopener" class="profile-link">{{ link.label }}</a>
            </div>
          </div>
        </div>

        <div v-if="filterTag" style="margin-bottom:16px; display:flex; align-items:center; gap:8px;">
          <span>Filtering by tag: <strong>#{{ filterTag }}</strong></span>
          <button class="btn btn-secondary btn-sm" @click="clearFilter">Clear</button>
        </div>

        <div class="post-grid" v-if="posts.length">
          <div v-for="post in posts" :key="post.id" class="post-thumb" @click="openPost(post)">
            <img v-if="post.images.length" :src="imgUrl(post.images[0].url)" :alt="post.caption" />
            <div v-else class="post-thumb post-thumb-empty">📷</div>
            <span v-if="post.images.length > 1" class="multi-badge">⧉</span>
          </div>
        </div>
        <div v-else class="empty-state">No posts yet.</div>
      </div>
      <div v-else class="page"><div class="spinner"></div></div>

      <div v-if="activePost" class="modal-overlay" @click.self="closePost">
        <button class="modal-close" @click="closePost">✕</button>
        <div class="modal">
          <div class="modal-media">
            <template v-if="activePost.images.length">
              <img :src="imgUrl(activePost.images[carouselIndex].url)" :alt="activePost.caption" />
              <button v-if="activePost.images.length > 1" class="carousel-btn carousel-prev" @click="prevImage">‹</button>
              <button v-if="activePost.images.length > 1" class="carousel-btn carousel-next" @click="nextImage">›</button>
              <div v-if="activePost.images.length > 1" class="carousel-dots">
                <button v-for="(_, i) in activePost.images" :key="i" class="carousel-dot" :class="{active: i === carouselIndex}" @click="carouselIndex = i"></button>
              </div>
            </template>
            <div v-else style="color:#666; padding:40px">No images</div>
          </div>
          <div class="modal-side">
            <div class="modal-header">{{ formatDate(activePost.created_at) }}</div>
            <div class="modal-body">
              <div class="modal-location" v-if="activePost.location">📍 {{ activePost.location }}</div>
              <div class="modal-caption">{{ activePost.caption }}</div>
              <div class="modal-tags">
                <span v-for="tag in activePost.tags" :key="tag.id" class="tag-chip" @click="closePost(); filterByTag(tag.name)">#{{ tag.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
}
