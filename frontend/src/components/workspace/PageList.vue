<script setup>
import { nextTick, reactive, ref } from 'vue'
import ContextMenu from '../ContextMenu.vue'
import Icon from '../Icon.vue'
import pageEditorIcon from '../../assets/icon/page-editor.svg'
import renameIcon from '../../assets/icon/rename.svg'
import deleteIcon from '../../assets/icon/delete.svg'

const props = defineProps({
  selectedPageID: {
    type: Number,
    default: null,
  },
  selectedSectionID: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['select-page', 'delete-page'])

const pages = ref([
  { id: 1, title: '1111' },
  { id: 2, title: '未命名' },
  { id: 3, title: '未命名' },
])
const contextMenu = reactive({
  open: false,
  x: 0,
  y: 0,
  pageID: null,
})
const contextMenuItems = [
  { type: 'action', id: 'rename', label: '重命名', icon: renameIcon },
  { type: 'action', id: 'delete', label: '删除', icon: deleteIcon },
]
const editingPageID = ref(null)
const editTitle = ref('')
const renameInput = ref(null)
let nextPageID = Math.max(...pages.value.map((page) => page.id), 0) + 1

function addPage() {
  if (!props.selectedSectionID) {
    return
  }

  const page = {
    id: nextPageID++,
    title: '未命名',
  }
  pages.value.push(page)
  emit('select-page', page.id)
}

function openPageMenu(event, page) {
  Object.assign(contextMenu, {
    open: true,
    x: event.clientX,
    y: event.clientY,
    pageID: page.id,
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

function startRename(page) {
  editingPageID.value = page.id
  editTitle.value = page.title
  nextTick(() => {
    renameInput.value?.focus()
    renameInput.value?.select()
  })
}

function confirmRename() {
  if (editingPageID.value === null) {
    return
  }

  const title = editTitle.value.trim()
  const page = pages.value.find((item) => item.id === editingPageID.value)
  if (title && page) {
    page.title = title
  }

  editingPageID.value = null
}

function cancelRename() {
  editingPageID.value = null
}

function handleContextAction(action) {
  const page = pages.value.find((item) => item.id === contextMenu.pageID)
  if (!page) {
    return
  }

  if (action.id === 'rename') {
    startRename(page)
    return
  }

  if (action.id === 'delete') {
    const pageIndex = pages.value.findIndex((item) => item.id === page.id)
    pages.value.splice(pageIndex, 1)
    emit('delete-page', page.id)
  }
}
</script>

<template>
  <section class="relative flex h-full w-60 shrink-0 flex-col bg-white">
    <div aria-hidden="true" class="absolute bottom-0 right-0 top-2 w-1 bg-[#f3f3f3]" />
    <header class="flex h-16 shrink-0 items-center px-3">
      <button
        type="button"
        class="inline-flex h-7 w-32 items-center justify-center gap-2 rounded-md border border-slate-300/80 bg-slate-50/80 text-sm text-violet-600 transition-[background-color,transform] hover:bg-violet-50 active:translate-y-px active:bg-violet-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-300/70 disabled:pointer-events-none disabled:cursor-default disabled:opacity-45"
        :disabled="!props.selectedSectionID"
        @click="addPage"
      >
        <Icon :src="pageEditorIcon" class="h-4 w-4 shrink-0" />
        <span>添加页</span>
      </button>
    </header>

    <div class="workspace-scroll mr-1 min-h-0 flex-1 overflow-y-auto px-3 pb-3">
      <template v-if="props.selectedSectionID">
        <div
          v-for="page in pages"
          :key="page.id"
          class="mb-1 flex h-11 w-full select-none items-center rounded-md px-4 text-left text-sm text-slate-600 transition-colors hover:bg-slate-100/80 active:bg-slate-300/70 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400/60"
          :class="{
            'bg-slate-200/80 font-semibold text-slate-900': props.selectedPageID === page.id,
          }"
          :role="editingPageID === page.id ? undefined : 'button'"
          :tabindex="editingPageID === page.id ? undefined : 0"
          @click="editingPageID !== page.id && emit('select-page', page.id)"
          @keydown.enter.prevent="editingPageID !== page.id && emit('select-page', page.id)"
          @contextmenu.prevent.stop="openPageMenu($event, page)"
        >
          <input
            v-if="editingPageID === page.id"
            :ref="setRenameInput"
            v-model="editTitle"
            type="text"
            class="h-8 min-w-0 flex-1 select-text border-b border-slate-400 bg-transparent px-1 text-sm font-normal outline-none"
            @click.stop
            @keydown.enter.prevent.stop="confirmRename"
            @keydown.escape.prevent.stop="cancelRename"
            @blur="confirmRename"
          />
          <span v-else class="min-w-0 truncate">{{ page.title }}</span>
        </div>
      </template>
    </div>
  </section>
  <ContextMenu
    :open="contextMenu.open"
    :x="contextMenu.x"
    :y="contextMenu.y"
    :items="contextMenuItems"
    @select="handleContextAction"
    @close="closeContextMenu"
  />
</template>
