<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import ConfirmDialog from '../ConfirmDialog.vue'
import ContextMenu from '../ContextMenu.vue'
import Icon from '../Icon.vue'
import { notebookApi } from '../../api/notebook.js'
import { sectionApi } from '../../api/section.js'
import panelIcon from '../../assets/icon/panel-left.svg'
import chevronIcon from '../../assets/icon/chevron-right.svg'
import notebookIcon from '../../assets/icon/notebook.svg'
import sectionIcon from '../../assets/icon/section.svg'
import homeIcon from '../../assets/icon/house.svg'
import notebookAddIcon from '../../assets/icon/notebook-add.svg'
import sectionAddIcon from '../../assets/icon/section-add.svg'
import renameIcon from '../../assets/icon/rename.svg'
import deleteIcon from '../../assets/icon/delete.svg'

const props = defineProps({
  expanded: {
    type: Boolean,
    required: true,
  },
  selectedNotebookID: {
    type: Number,
    default: null,
  },
  selectedSectionID: {
    type: Number,
    default: null,
  },
})

const emit = defineEmits([
  'toggle',
  'select-notebook',
  'select-section',
  'delete-notebook',
  'delete-section',
])

const colors = ['#7967c3', '#4c88c7', '#5a9b8c', '#d0a442', '#de8c56', '#b06b87']
const notebooks = ref([])
const loadingNotebooks = ref(false)
const creatingNotebook = ref(false)
const sidebarError = ref('')
const creatingSections = reactive(new Set())
const deletingNotebooks = reactive(new Set())
const deletingSections = reactive(new Set())
const sectionLoads = new Map()
const updateQueues = new Map()

const contextMenu = reactive({
  open: false,
  x: 0,
  y: 0,
  type: '',
  notebookID: null,
  sectionID: null,
})
const deleteDialog = reactive({
  open: false,
  type: '',
  notebookID: null,
  sectionID: null,
  name: '',
  loading: false,
  error: '',
})
const editing = ref(null)
const editName = ref('')
const renameInput = ref(null)

onMounted(loadNotebooks)

function describeError(action, error) {
  const message = error instanceof Error ? error.message : String(error ?? '')
  return message ? `${action}失败：${message}` : `${action}失败，请稍后重试`
}

function createNotebookState(notebook, options = {}) {
  return {
    ...notebook,
    expanded: options.expanded ?? false,
    sections: options.sections ?? [],
    loaded: options.loaded ?? false,
    loading: false,
  }
}

async function loadNotebooks() {
  if (loadingNotebooks.value) {
    return
  }

  loadingNotebooks.value = true
  sidebarError.value = ''
  try {
    const result = await notebookApi.list()
    notebooks.value = (result ?? []).map((notebook) => createNotebookState(notebook))
  } catch (error) {
    sidebarError.value = describeError('加载笔记本', error)
  } finally {
    loadingNotebooks.value = false
  }
}

const contextMenuItems = computed(() => {
  const notebook = findNotebook(contextMenu.notebookID)

  if (!notebook) {
    return []
  }

  if (contextMenu.type === 'notebook') {
    return [
      { type: 'action', id: 'new-section', label: '新建 Section', icon: sectionAddIcon },
      { type: 'separator' },
      { type: 'action', id: 'rename', label: '重命名', icon: renameIcon },
      { type: 'action', id: 'delete', label: '删除', icon: deleteIcon },
      { type: 'separator' },
      { type: 'colors', current: notebook.color, options: colors },
    ]
  }

  const section = notebook.sections.find((item) => item.id === contextMenu.sectionID)
  if (!section) {
    return []
  }

  return [
    { type: 'action', id: 'rename', label: '重命名', icon: renameIcon },
    { type: 'action', id: 'delete', label: '删除', icon: deleteIcon },
    { type: 'separator' },
    { type: 'colors', current: section.color, options: colors },
  ]
})

const deleteDialogTitle = computed(() => (
  deleteDialog.type === 'notebook' ? '删除笔记本' : '删除分区'
))

const deleteDialogMessage = computed(() => {
  if (deleteDialog.type === 'notebook') {
    return `确定删除笔记本「${deleteDialog.name}」吗？其下所有分区和页面也会被删除。`
  }
  return `确定删除分区「${deleteDialog.name}」吗？其下所有页面也会被删除。`
})

function findNotebook(notebookID) {
  return notebooks.value.find((notebook) => notebook.id === notebookID)
}

async function ensureSectionsLoaded(notebook) {
  if (notebook.loaded) {
    return true
  }

  const existingLoad = sectionLoads.get(notebook.id)
  if (existingLoad) {
    return existingLoad
  }

  notebook.loading = true
  sidebarError.value = ''
  const load = (async () => {
    try {
      const sections = await sectionApi.list(notebook.id)
      if (findNotebook(notebook.id) !== notebook) {
        return false
      }

      notebook.sections = sections ?? []
      notebook.loaded = true
      return true
    } catch (error) {
      if (findNotebook(notebook.id) === notebook) {
        sidebarError.value = describeError('加载分区', error)
      }
      return false
    } finally {
      if (findNotebook(notebook.id) === notebook) {
        notebook.loading = false
      }
      if (sectionLoads.get(notebook.id) === load) {
        sectionLoads.delete(notebook.id)
      }
    }
  })()

  sectionLoads.set(notebook.id, load)
  return load
}

async function toggleNotebook(notebook) {
  notebook.expanded = !notebook.expanded
  if (notebook.expanded) {
    await ensureSectionsLoaded(notebook)
  }
}

async function createNotebook() {
  if (creatingNotebook.value || loadingNotebooks.value) {
    return
  }

  creatingNotebook.value = true
  sidebarError.value = ''
  try {
    const created = await notebookApi.create('新笔记本', colors[0])
    const notebook = createNotebookState(created, {
      expanded: true,
      loaded: true,
    })
    notebooks.value.push(notebook)
    emit('select-notebook', notebook.id)
  } catch (error) {
    sidebarError.value = describeError('新建笔记本', error)
  } finally {
    creatingNotebook.value = false
  }
}

async function runQueuedUpdate(key, operation) {
  const previous = updateQueues.get(key)
  const current = (async () => {
    if (previous) {
      await previous
    }
    return operation()
  })()

  updateQueues.set(key, current)
  try {
    return await current
  } finally {
    if (updateQueues.get(key) === current) {
      updateQueues.delete(key)
    }
  }
}

function updateNotebook(notebookID, changes) {
  return runQueuedUpdate(`notebook:${notebookID}`, async () => {
    const notebook = findNotebook(notebookID)
    if (!notebook || deletingNotebooks.has(notebookID)) {
      return false
    }

    sidebarError.value = ''
    const name = changes.name ?? notebook.name
    const color = changes.color ?? notebook.color
    try {
      await notebookApi.update(notebook.id, name, color)
      if (findNotebook(notebook.id) === notebook) {
        notebook.name = name
        notebook.color = color
      }
      return true
    } catch (error) {
      sidebarError.value = describeError('更新笔记本', error)
      return false
    }
  })
}

function updateSection(notebookID, sectionID, changes) {
  return runQueuedUpdate(`section:${sectionID}`, async () => {
    const notebook = findNotebook(notebookID)
    const section = notebook?.sections.find((item) => item.id === sectionID)
    if (!section || deletingSections.has(sectionID)) {
      return false
    }

    sidebarError.value = ''
    const name = changes.name ?? section.name
    const color = changes.color ?? section.color
    try {
      await sectionApi.update(section.id, name, color)
      const currentNotebook = findNotebook(notebookID)
      const currentSection = currentNotebook?.sections.find((item) => item.id === sectionID)
      if (currentSection === section) {
        section.name = name
        section.color = color
      }
      return true
    } catch (error) {
      sidebarError.value = describeError('更新分区', error)
      return false
    }
  })
}

function openNotebookMenu(event, notebook) {
  Object.assign(contextMenu, {
    open: true,
    x: event.clientX,
    y: event.clientY,
    type: 'notebook',
    notebookID: notebook.id,
    sectionID: null,
  })
}

function openSectionMenu(event, notebook, section) {
  Object.assign(contextMenu, {
    open: true,
    x: event.clientX,
    y: event.clientY,
    type: 'section',
    notebookID: notebook.id,
    sectionID: section.id,
  })
}

function closeContextMenu() {
  contextMenu.open = false
}

function resetDeleteDialog() {
  if (deleteDialog.loading) {
    return
  }

  Object.assign(deleteDialog, {
    open: false,
    type: '',
    notebookID: null,
    sectionID: null,
    name: '',
    loading: false,
    error: '',
  })
}

function openDeleteDialog(type, notebook, section = null) {
  if (deleteDialog.loading) {
    return
  }

  closeContextMenu()
  Object.assign(deleteDialog, {
    open: true,
    type,
    notebookID: notebook.id,
    sectionID: section?.id ?? null,
    name: section?.name ?? notebook.name,
    loading: false,
    error: '',
  })
}

function setRenameInput(element) {
  if (element) {
    renameInput.value = element
  }
}

function isEditing(type, id) {
  return editing.value?.type === type && editing.value.id === id
}

function startRename(type, notebookID, id, name) {
  editing.value = { type, notebookID, id }
  editName.value = name
  nextTick(() => {
    renameInput.value?.focus()
    renameInput.value?.select()
  })
}

async function confirmRename() {
  if (!editing.value) {
    return
  }

  const target = editing.value
  const name = editName.value.trim()
  editing.value = null
  if (!name) {
    return
  }

  if (target.type === 'notebook') {
    await updateNotebook(target.id, { name })
  } else {
    await updateSection(target.notebookID, target.id, { name })
  }
}

function cancelRename() {
  editing.value = null
}

async function createSection(notebook) {
  if (creatingSections.has(notebook.id) || deletingNotebooks.has(notebook.id)) {
    return
  }

  creatingSections.add(notebook.id)
  sidebarError.value = ''
  try {
    notebook.expanded = true
    if (!(await ensureSectionsLoaded(notebook))) {
      return
    }

    const created = await sectionApi.create(notebook.id, '新分区', notebook.color)
    if (findNotebook(notebook.id) === notebook) {
      notebook.sections.push(created)
    }
  } catch (error) {
    sidebarError.value = describeError('新建分区', error)
  } finally {
    creatingSections.delete(notebook.id)
  }
}

async function deleteNotebook(notebook) {
  if (deletingNotebooks.has(notebook.id)) {
    return { ok: false, error: '该笔记本正在删除，请稍候' }
  }

  deletingNotebooks.add(notebook.id)
  sidebarError.value = ''
  try {
    const pendingUpdate = updateQueues.get(`notebook:${notebook.id}`)
    if (pendingUpdate) {
      await pendingUpdate
    }
    await notebookApi.remove(notebook.id)

    const notebookIndex = notebooks.value.findIndex((item) => item === notebook)
    if (notebookIndex !== -1) {
      notebooks.value.splice(notebookIndex, 1)
      emit('delete-notebook', notebook.id)
    }
    return { ok: true, error: '' }
  } catch (error) {
    return { ok: false, error: describeError('删除笔记本', error) }
  } finally {
    deletingNotebooks.delete(notebook.id)
  }
}

async function deleteSection(notebook, sectionID) {
  if (deletingSections.has(sectionID)) {
    return { ok: false, error: '该分区正在删除，请稍候' }
  }

  deletingSections.add(sectionID)
  sidebarError.value = ''
  try {
    const pendingUpdate = updateQueues.get(`section:${sectionID}`)
    if (pendingUpdate) {
      await pendingUpdate
    }
    await sectionApi.remove(sectionID)

    const currentNotebook = findNotebook(notebook.id)
    const sectionIndex = currentNotebook?.sections.findIndex((item) => item.id === sectionID) ?? -1
    if (sectionIndex !== -1) {
      currentNotebook.sections.splice(sectionIndex, 1)
      emit('delete-section', { notebookID: notebook.id, sectionID })
    }
    return { ok: true, error: '' }
  } catch (error) {
    return { ok: false, error: describeError('删除分区', error) }
  } finally {
    deletingSections.delete(sectionID)
  }
}

async function confirmDelete() {
  if (!deleteDialog.open || deleteDialog.loading) {
    return
  }

  const type = deleteDialog.type
  const notebookID = deleteDialog.notebookID
  const sectionID = deleteDialog.sectionID
  const notebook = findNotebook(notebookID)
  const section = notebook?.sections.find((item) => item.id === sectionID)
  if (!notebook || (type === 'section' && !section)) {
    resetDeleteDialog()
    return
  }

  deleteDialog.loading = true
  deleteDialog.error = ''
  const result = type === 'notebook'
    ? await deleteNotebook(notebook)
    : await deleteSection(notebook, sectionID)

  deleteDialog.loading = false
  if (result.ok) {
    resetDeleteDialog()
  } else {
    deleteDialog.error = result.error
  }
}

function handleContextAction(action) {
  const notebook = findNotebook(contextMenu.notebookID)
  if (!notebook) {
    return
  }

  if (action.id === 'color') {
    if (contextMenu.type === 'notebook') {
      void updateNotebook(notebook.id, { color: action.color })
    } else {
      const section = notebook.sections.find((item) => item.id === contextMenu.sectionID)
      if (section) {
        void updateSection(notebook.id, section.id, { color: action.color })
      }
    }
    return
  }

  if (action.id === 'new-section') {
    void createSection(notebook)
    return
  }

  if (action.id === 'rename') {
    if (contextMenu.type === 'notebook') {
      startRename('notebook', notebook.id, notebook.id, notebook.name)
    } else {
      const section = notebook.sections.find((item) => item.id === contextMenu.sectionID)
      if (section) {
        startRename('section', notebook.id, section.id, section.name)
      }
    }
    return
  }

  if (action.id !== 'delete') {
    return
  }

  if (contextMenu.type === 'notebook') {
    openDeleteDialog('notebook', notebook)
    return
  }

  const section = notebook.sections.find((item) => item.id === contextMenu.sectionID)
  if (section) {
    openDeleteDialog('section', notebook, section)
  }
}

</script>

<template>
  <aside
    class="flex h-full shrink-0 flex-col overflow-hidden border-r border-slate-300/55 bg-[#e8edf1]"
    :class="expanded ? 'w-64' : 'w-14'"
  >
    <div class="flex h-14 shrink-0 items-center px-2.5" :class="expanded ? 'justify-start' : 'justify-center'">
      <button
        type="button"
        class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-slate-600 transition-colors hover:bg-white/55 active:bg-slate-300/55 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400/60"
        :aria-label="expanded ? '折叠侧边栏' : '展开侧边栏'"
        @click="emit('toggle')"
      >
        <img :src="panelIcon" alt="" class="h-5 w-5" />
      </button>

    </div>

    <div
      v-if="expanded"
      class="workspace-scroll min-h-0 flex-1 overflow-y-auto px-2 pb-3"
      :aria-busy="loadingNotebooks"
    >
      <p v-if="sidebarError" role="alert" class="px-2 pb-2 text-xs text-red-600">
        {{ sidebarError }}
      </p>
      <p v-else-if="loadingNotebooks" class="px-2 pb-2 text-xs text-slate-500">
        正在加载笔记本…
      </p>

      <div v-for="notebook in notebooks" :key="notebook.id" class="mb-1">
        <div
          class="flex h-9 w-full min-w-0 items-center gap-1.5 rounded-lg px-2 text-left text-sm font-medium text-slate-700 hover:bg-white/50"
          :class="{ 'bg-white/65 text-slate-900': props.selectedNotebookID === notebook.id }"
          @contextmenu.prevent.stop="openNotebookMenu($event, notebook)"
        >
          <button
            type="button"
            class="flex h-8 w-4 shrink-0 items-center justify-center focus:outline-none"
            :aria-label="notebook.expanded ? `折叠 ${notebook.name}` : `展开 ${notebook.name}`"
            @click="toggleNotebook(notebook)"
          >
            <img
              :src="chevronIcon"
              alt=""
              class="h-3.5 w-3.5 opacity-65 transition-transform"
              :class="{ 'rotate-90': notebook.expanded }"
            />
          </button>
          <div v-if="isEditing('notebook', notebook.id)" class="flex min-w-0 flex-1 items-center gap-1.5">
            <Icon :src="notebookIcon" :color="notebook.color" class="h-4 w-4 shrink-0" />
            <input
              :ref="setRenameInput"
              v-model="editName"
              type="text"
              class="h-7 min-w-0 flex-1 border-b border-slate-400 bg-transparent px-1 text-sm outline-none"
              @click.stop
              @keydown.enter.prevent.stop="confirmRename"
              @keydown.escape.prevent.stop="cancelRename"
              @blur="confirmRename"
            />
          </div>
          <button
            v-else
            type="button"
            class="flex h-full min-w-0 flex-1 items-center gap-1.5 rounded-md text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400/60"
            @click="emit('select-notebook', notebook.id)"
          >
            <Icon :src="notebookIcon" :color="notebook.color" class="h-4 w-4 shrink-0" />
            <span class="min-w-0 truncate">{{ notebook.name }}</span>
          </button>
        </div>

        <div v-if="notebook.expanded" class="mt-1.5 flex flex-col gap-1">
          <p v-if="notebook.loading" class="h-8 pr-2 pl-12 text-xs leading-8 text-slate-500">
            正在加载分区…
          </p>
          <div
            v-for="section in notebook.sections"
            :key="section.id"
            class="flex h-8 w-full min-w-0 select-none items-center gap-1.5 rounded-md pr-2 pl-7 text-left text-sm text-slate-600 transition-colors hover:bg-white/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400/60"
            :class="{ 'bg-white/65 font-semibold text-slate-900': props.selectedSectionID === section.id }"
            :role="isEditing('section', section.id) ? undefined : 'button'"
            :tabindex="isEditing('section', section.id) ? undefined : 0"
            @click="!isEditing('section', section.id) && emit('select-section', { notebookID: notebook.id, sectionID: section.id })"
            @keydown.enter.prevent="!isEditing('section', section.id) && emit('select-section', { notebookID: notebook.id, sectionID: section.id })"
            @contextmenu.prevent.stop="openSectionMenu($event, notebook, section)"
          >
            <span class="h-3 w-3 shrink-0" />
            <Icon :src="sectionIcon" :color="section.color" class="h-6 w-6 shrink-0" />
            <input
              v-if="isEditing('section', section.id)"
              :ref="setRenameInput"
              v-model="editName"
              type="text"
              class="h-7 min-w-0 flex-1 select-text border-b border-slate-400 bg-transparent px-1 text-sm font-normal outline-none"
              @click.stop
              @keydown.enter.prevent.stop="confirmRename"
              @keydown.escape.prevent.stop="cancelRename"
              @blur="confirmRename"
            />
            <span v-else class="min-w-0 truncate">{{ section.name }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="expanded" class="flex h-14 shrink-0 items-center border-t border-slate-300/45">
      <div class="flex flex-1 justify-center">
        <button
          type="button"
          aria-label="主页"
          class="flex h-9 w-9 items-center justify-center rounded-lg text-slate-600 transition-colors hover:bg-white/55 active:bg-slate-300/55 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400/60"
        >
          <Icon :src="homeIcon" class="h-5 w-5" />
        </button>
      </div>
      <div aria-hidden="true" class="h-6 w-px shrink-0 bg-slate-300/70" />
      <div class="flex flex-1 justify-center">
        <button
          type="button"
          aria-label="新建笔记本"
          class="flex h-9 w-9 items-center justify-center rounded-lg text-slate-600 transition-colors hover:bg-white/55 active:bg-slate-300/55 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400/60 disabled:pointer-events-none disabled:opacity-45"
          :disabled="creatingNotebook || loadingNotebooks"
          @click="createNotebook"
        >
          <Icon :src="notebookAddIcon" class="h-5 w-5" />
        </button>
      </div>
    </div>
  </aside>
  <ContextMenu
    :open="contextMenu.open"
    :x="contextMenu.x"
    :y="contextMenu.y"
    :items="contextMenuItems"
    @select="handleContextAction"
    @close="closeContextMenu"
  />
  <ConfirmDialog
    :open="deleteDialog.open"
    :title="deleteDialogTitle"
    :message="deleteDialogMessage"
    confirm-text="删除"
    :loading="deleteDialog.loading"
    :error="deleteDialog.error"
    @confirm="confirmDelete"
    @cancel="resetDeleteDialog"
  />
</template>
