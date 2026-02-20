import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, imgUrl } from '../api.js'

export default {
  setup() {
    const route = useRoute()
    const router = useRouter()
    const post = ref(null)
    const form = reactive({ caption: '', location: '', published: false })
    const tagInput = ref('')
    const tags = ref([])
    const saving = ref(false)
    const uploadingImages = ref(false)
    const saveMsg = ref('')

    async function load() {
      const res = await api(`/posts/${route.params.id}`)
      if (!res.ok) { router.push('/feed'); return }
      post.value = await res.json()
      form.caption = post.value.caption
      form.location = post.value.location || ''
      form.published = post.value.published
      tags.value = post.value.tags.map(t => t.name)
    }

    function addTag() {
      const name = tagInput.value.trim().toLowerCase()
      if (name && !tags.value.includes(name)) tags.value.push(name)
      tagInput.value = ''
    }

    function removeTag(name) { tags.value = tags.value.filter(t => t !== name) }

    async function save() {
      saving.value = true
      saveMsg.value = ''
      try {
        const res = await api(`/posts/${post.value.id}`, {
          method: 'PATCH',
          body: JSON.stringify({ caption: form.caption, location: form.location || null, published: form.published, tags: tags.value })
        })
        post.value = await res.json()
        saveMsg.value = 'Saved!'
        setTimeout(() => saveMsg.value = '', 2000)
      } finally {
        saving.value = false
      }
    }

    async function uploadImages(e) {
      const files = e.target.files
      if (!files.length) return
      uploadingImages.value = true
      const fd = new FormData()
      for (const f of files) fd.append('files', f)
      const res = await api(`/posts/${post.value.id}/images`, { method: 'POST', body: fd })
      post.value = await res.json()
      uploadingImages.value = false
      e.target.value = ''
    }

    async function deleteImage(imgId) {
      const res = await api(`/posts/${post.value.id}/images/${imgId}`, { method: 'DELETE' })
      post.value = await res.json()
    }

    async function moveImage(imgId, direction) {
      const imgs = [...post.value.images]
      const idx = imgs.findIndex(i => i.id === imgId)
      if (idx < 0) return
      const newIdx = idx + direction
      if (newIdx < 0 || newIdx >= imgs.length) return
      ;[imgs[idx], imgs[newIdx]] = [imgs[newIdx], imgs[idx]]
      const res = await api(`/posts/${post.value.id}/images/reorder`, {
        method: 'PATCH',
        body: JSON.stringify({ image_ids: imgs.map(i => i.id) })
      })
      post.value = await res.json()
    }

    onMounted(load)

    return { post, form, tagInput, tags, saving, uploadingImages, saveMsg, addTag, removeTag, save, uploadImages, deleteImage, moveImage, imgUrl }
  },
  template: `
    <div>
      <nav-bar />
      <div class="page" v-if="post">
        <div class="edit-header">
          <router-link to="/feed" class="btn btn-secondary btn-sm">← Back</router-link>
          <h1>Edit Post #{{ post.id }}</h1>
        </div>

        <div class="card" style="padding:24px; margin-bottom:24px;">
          <div class="form-group">
            <label>Caption</label>
            <textarea v-model="form.caption" rows="4" placeholder="Write a caption…"></textarea>
          </div>
          <div class="form-group">
            <label>Location</label>
            <input type="text" v-model="form.location" placeholder="City, Country" />
          </div>
          <div class="form-group">
            <label>Tags</label>
            <div class="tags-input-row">
              <input type="text" v-model="tagInput" placeholder="Add tag" @keydown.enter.prevent="addTag" @keydown.comma.prevent="addTag" />
              <button class="btn btn-secondary btn-sm" @click="addTag">Add</button>
            </div>
            <div class="tags-list">
              <span v-for="t in tags" :key="t" class="tag-remove">
                #{{ t }}<button @click="removeTag(t)">×</button>
              </span>
            </div>
          </div>
          <div class="form-group" style="display:flex; align-items:center; gap:10px;">
            <input type="checkbox" id="pub" v-model="form.published" style="width:auto;" />
            <label for="pub" style="margin:0; font-weight:400;">Published (visible to public)</label>
          </div>
          <div style="display:flex; align-items:center; gap:12px;">
            <button class="btn btn-primary" @click="save" :disabled="saving">
              <span v-if="saving" class="spinner"></span>
              <span v-else>Save</span>
            </button>
            <span style="color:#2ecc71; font-weight:600;" v-if="saveMsg">{{ saveMsg }}</span>
          </div>
        </div>

        <div class="card" style="padding:24px;">
          <h2 style="font-size:16px; font-weight:700; margin-bottom:16px;">Images</h2>
          <div class="image-grid" v-if="post.images.length">
            <div v-for="(img, i) in post.images" :key="img.id" class="image-item">
              <img :src="imgUrl(img.filename)" :alt="'Image ' + (i+1)" />
              <span class="img-order">{{ i + 1 }}</span>
              <div class="img-actions">
                <button class="btn btn-secondary btn-sm" @click="moveImage(img.id, -1)" :disabled="i === 0">←</button>
                <button class="btn btn-danger btn-sm" @click="deleteImage(img.id)">✕</button>
                <button class="btn btn-secondary btn-sm" @click="moveImage(img.id, 1)" :disabled="i === post.images.length - 1">→</button>
              </div>
            </div>
          </div>
          <div v-else class="empty-state" style="padding:24px 0">No images yet.</div>
          <div style="margin-top:12px; display:flex; align-items:center; gap:12px;">
            <label class="btn btn-secondary" style="cursor:pointer;">
              <span v-if="uploadingImages" class="spinner"></span>
              <span v-else>Upload images</span>
              <input type="file" multiple accept="image/*" style="display:none;" @change="uploadImages" :disabled="uploadingImages" />
            </label>
          </div>
        </div>
      </div>
      <div v-else class="page"><div class="spinner"></div></div>
    </div>
  `
}
