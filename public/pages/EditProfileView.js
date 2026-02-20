import { ref, reactive, onMounted } from 'vue'
import { api, imgUrl } from '../api.js'

export default {
  setup() {
    const profile = ref(null)
    const form = reactive({ name: '', bio: '', links: [] })
    const saving = ref(false)
    const uploadingAvatar = ref(false)
    const saveMsg = ref('')
    const newLink = reactive({ label: '', url: '' })

    async function load() {
      const res = await api('/profile')
      profile.value = await res.json()
      form.name = profile.value.name
      form.bio = profile.value.bio
      form.links = profile.value.links.map(l => ({ ...l }))
    }

    async function save() {
      saving.value = true
      saveMsg.value = ''
      try {
        const res = await api('/profile', {
          method: 'PATCH',
          body: JSON.stringify({ name: form.name, bio: form.bio, links: form.links })
        })
        profile.value = await res.json()
        saveMsg.value = 'Saved!'
        setTimeout(() => saveMsg.value = '', 2000)
      } finally {
        saving.value = false
      }
    }

    function addLink() {
      if (!newLink.label || !newLink.url) return
      form.links.push({ label: newLink.label, url: newLink.url })
      newLink.label = ''
      newLink.url = ''
    }

    function removeLink(i) { form.links.splice(i, 1) }

    async function uploadAvatar(e) {
      const file = e.target.files[0]
      if (!file) return
      uploadingAvatar.value = true
      const fd = new FormData()
      fd.append('file', file)
      const res = await api('/profile/avatar', { method: 'POST', body: fd })
      profile.value = await res.json()
      uploadingAvatar.value = false
      e.target.value = ''
    }

    onMounted(load)

    return { profile, form, saving, uploadingAvatar, saveMsg, newLink, save, addLink, removeLink, uploadAvatar, imgUrl }
  },
  template: `
    <div>
      <nav-bar />
      <div class="page" v-if="profile">
        <div class="edit-header" style="margin-bottom:24px;">
          <router-link to="/feed" class="btn btn-secondary btn-sm">← Back</router-link>
          <h1>Edit Profile</h1>
        </div>

        <div class="card" style="padding:24px; margin-bottom:24px;">
          <h2 style="font-size:16px; font-weight:700; margin-bottom:16px;">Avatar</h2>
          <div style="display:flex; align-items:center; gap:20px; margin-bottom:12px;">
            <img v-if="profile.avatar_filename" :src="imgUrl(profile.avatar_filename)" style="width:80px;height:80px;border-radius:50%;object-fit:cover;" />
            <div v-else style="width:80px;height:80px;border-radius:50%;background:var(--border);display:flex;align-items:center;justify-content:center;font-size:32px;">👤</div>
            <label class="btn btn-secondary" style="cursor:pointer;">
              <span v-if="uploadingAvatar" class="spinner"></span>
              <span v-else>Change avatar</span>
              <input type="file" accept="image/*" style="display:none;" @change="uploadAvatar" :disabled="uploadingAvatar" />
            </label>
          </div>
        </div>

        <div class="card" style="padding:24px;">
          <div class="form-group">
            <label>Name</label>
            <input type="text" v-model="form.name" placeholder="Your name" />
          </div>
          <div class="form-group">
            <label>Bio</label>
            <textarea v-model="form.bio" rows="4" placeholder="Tell your story…"></textarea>
          </div>

          <div class="form-group">
            <label>Links</label>
            <div class="links-list">
              <div v-for="(link, i) in form.links" :key="i" class="link-row">
                <input type="text" v-model="link.label" placeholder="Label" style="max-width:140px;" />
                <input type="text" v-model="link.url" placeholder="https://…" />
                <button class="btn btn-danger btn-sm" @click="removeLink(i)">✕</button>
              </div>
            </div>
            <div class="link-row">
              <input type="text" v-model="newLink.label" placeholder="Label" style="max-width:140px;" />
              <input type="text" v-model="newLink.url" placeholder="https://…" />
              <button class="btn btn-secondary btn-sm" @click="addLink">Add</button>
            </div>
          </div>

          <div style="display:flex; align-items:center; gap:12px; margin-top:8px;">
            <button class="btn btn-primary" @click="save" :disabled="saving">
              <span v-if="saving" class="spinner"></span>
              <span v-else>Save profile</span>
            </button>
            <span style="color:#2ecc71; font-weight:600;" v-if="saveMsg">{{ saveMsg }}</span>
          </div>
        </div>
      </div>
      <div v-else class="page"><div class="spinner"></div></div>
    </div>
  `
}
