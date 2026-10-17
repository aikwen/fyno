<script setup>
import { computed, nextTick, reactive, ref } from 'vue'
import ContextMenu from '../ContextMenu.vue'
import Icon from '../Icon.vue'
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
    type: String,
    default: '',
  },
  selectedSectionID: {
    type: String,
    default: '',
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

const notebooks = ref([
  {
    id: 'personal',
    name: 'Personal Notes',
    color: '#7967c3',
    expanded: true,
    sections: [
      { id: 'quick-notes', name: 'Quick Notes', color: '#de8c56' },
      { id: 'projects', name: 'Projects', color: '#5a9b8c' },
      { id: 'fyno-v2', name: 'Fyno v2', color: '#5a9b8c' },
      { id: 'reading-list', name: 'Reading List', color: '#b06b87' },
    ],
  },
  {
    id: 'work',
    name: 'Work Notebook With A Longer Name',
    color: '#4c88c7',
    expanded: false,
    sections: [
      { id: 'meetings', name: 'Meetings', color: '#4c88c7' },
      { id: 'planning', name: 'Planning', color: '#d0a442' },
    ],
  },
  {
    id: 'archive',
    name: 'Archive',
    color: '#768390',
    expanded: true,
    sections: [{ id: 'ideas', name: 'Ideas', color: '#768390' }],
  },
])

const contextMenu = reactive({
  open: false,
  x: 0,
  y: 0,
  type: '',
  notebookID: '',
  sectionID: '',
})
const editing = ref(null)
const editName = ref('')
const renameInput = ref(null)
let nextSectionID = 1

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

function findNotebook(notebookID) {
  return notebooks.value.find((notebook) => notebook.id === notebookID)
}

function openNotebookMenu(event, notebook) {
  Object.assign(contextMenu, {
    open: true,
    x: event.clientX,
    y: event.clientY,
    type: 'notebook',
    notebookID: notebook.id,
    sectionID: '',
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

function confirmRename() {
  if (!editing.value) {
    return
  }

  const name = editName.value.trim()
  const notebook = findNotebook(editing.value.notebookID)

  if (name && notebook) {
    if (editing.value.type === 'notebook') {
      notebook.name = name
    } else {
      const section = notebook.sections.find((item) => item.id === editing.value.id)
      if (section) {
        section.name = name
      }
    }
  }

  editing.value = null
}

function cancelRename() {
  editing.value = null
}

function handleContextAction(action) {
  const notebook = findNotebook(contextMenu.notebookID)
  if (!notebook) {
    return
  }

  if (action.id === 'color') {
    if (contextMenu.type === 'notebook') {
      notebook.color = action.color
    } else {
      const section = notebook.sections.find((item) => item.id === contextMenu.sectionID)
      if (section) {
        section.color = action.color
      }
    }
    return
  }

  if (action.id === 'new-section') {
    notebook.sections.push({
      id: `mock-section-${nextSectionID++}`,
      name: '新分区',
      color: notebook.color,
    })
    notebook.expanded = true
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
    const notebookIndex = notebooks.value.findIndex((item) => item.id === notebook.id)
    const sectionIDs = notebook.sections.map((section) => section.id)
    notebooks.value.splice(notebookIndex, 1)
    emit('delete-notebook', { notebookID: notebook.id, sectionIDs })
    return
  }

  const sectionIndex = notebook.sections.findIndex((item) => item.id === contextMenu.sectionID)
  if (sectionIndex !== -1) {
    const [section] = notebook.sections.splice(sectionIndex, 1)
    emit('delete-section', { notebookID: notebook.id, sectionID: section.id })
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

    <div v-if="expanded" class="sidebar-scroll min-h-0 flex-1 overflow-y-auto px-2 pb-3">
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
            @click="notebook.expanded = !notebook.expanded"
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
          class="flex h-9 w-9 items-center justify-center rounded-lg text-slate-600 transition-colors hover:bg-white/55 active:bg-slate-300/55 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400/60"
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
</template>

<style scoped>
.sidebar-scroll {
  scrollbar-color: transparent transparent;
  scrollbar-gutter: stable;
  scrollbar-width: thin;
}

.sidebar-scroll:hover {
  scrollbar-color: #aeb7c2 transparent;
}

.sidebar-scroll::-webkit-scrollbar {
  width: 4px;
}

.sidebar-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-scroll::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: transparent;
}

.sidebar-scroll:hover::-webkit-scrollbar-thumb {
  background: #aeb7c2;
}
</style>
