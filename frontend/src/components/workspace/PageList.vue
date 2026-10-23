<script setup>
import { nextTick, reactive, ref, watch } from 'vue'
import ContextMenu from '../ContextMenu.vue'
import Icon from '../Icon.vue'
import { pageApi } from '../../api/page.js'
import pageEditorIcon from '../../assets/icon/page-editor.svg'
import renameIcon from '../../assets/icon/rename.svg'
import deleteIcon from '../../assets/icon/delete.svg'

const props = defineProps({
  selectedPageID: {
    type: Number,
    default: null,
  },
  selectedSectionID: {
    type: Number,
    default: null,
  },
})

const emit = defineEmits(['select-page', 'delete-page'])

const pages = ref([])
const loadingPages = ref(false)
const creatingPage = ref(false)
const pageError = ref('')
const updatingPages = reactive(new Set())
const deletingPages = reactive(new Set())
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
let pageRequest = 0

watch(
  () => props.selectedSectionID,
  (sectionID) => {
    void loadPages(sectionID)
  },
  { immediate: true },
)

function describeError(action, error) {
  const message = error instanceof Error ? error.message : String(error ?? '')
  return message ? `${action}失败：${message}` : `${action}失败，请稍后重试`
}

async function loadPages(sectionID) {
  const request = ++pageRequest
  pages.value = []
  pageError.value = ''
  editingPageID.value = null
  contextMenu.open = false

  if (sectionID === null) {
    loadingPages.value = false
    return
  }

  loadingPages.value = true
  try {
    const result = await pageApi.list(sectionID)
    if (request === pageRequest && props.selectedSectionID === sectionID) {
      pages.value = result ?? []
    }
  } catch (error) {
    if (request === pageRequest && props.selectedSectionID === sectionID) {
      pageError.value = describeError('加载页面', error)
    }
  } finally {
    if (request === pageRequest) {
      loadingPages.value = false
    }
  }
}

async function addPage() {
  const sectionID = props.selectedSectionID
  if (sectionID === null || loadingPages.value || creatingPage.value) {
    return
  }

  creatingPage.value = true
  pageError.value = ''
  try {
    const page = await pageApi.create(sectionID, '未命名')
    if (props.selectedSectionID === sectionID) {
      pages.value.push(page)
      emit('select-page', page.id)
    }
  } catch (error) {
    if (props.selectedSectionID === sectionID) {
      pageError.value = describeError('添加页面', error)
    }
  } finally {
    creatingPage.value = false
  }
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

async function confirmRename() {
  if (editingPageID.value === null) {
    return
  }

  const pageID = editingPageID.value
  const sectionID = props.selectedSectionID
  const title = editTitle.value.trim()
  editingPageID.value = null
  const page = pages.value.find((item) => item.id === pageID)
  if (!title || !page || title === page.title || updatingPages.has(pageID)) {
    return
  }

  updatingPages.add(pageID)
  pageError.value = ''
  try {
    await pageApi.update(pageID, title)
    if (props.selectedSectionID === sectionID) {
      const currentPage = pages.value.find((item) => item.id === pageID)
      if (currentPage === page) {
        page.title = title
      }
    }
  } catch (error) {
    if (props.selectedSectionID === sectionID) {
      pageError.value = describeError('重命名页面', error)
    }
  } finally {
    updatingPages.delete(pageID)
  }
}

function cancelRename() {
  editingPageID.value = null
}

async function deletePage(page) {
  const sectionID = props.selectedSectionID
  if (deletingPages.has(page.id) || updatingPages.has(page.id)) {
    return
  }

  deletingPages.add(page.id)
  pageError.value = ''
  try {
    await pageApi.remove(page.id)
    if (props.selectedSectionID === sectionID) {
      const pageIndex = pages.value.findIndex((item) => item.id === page.id)
      if (pageIndex !== -1) {
        pages.value.splice(pageIndex, 1)
      }
    }
    emit('delete-page', page.id)
  } catch (error) {
    if (props.selectedSectionID === sectionID) {
      pageError.value = describeError('删除页面', error)
    }
  } finally {
    deletingPages.delete(page.id)
  }
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
    void deletePage(page)
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
        :disabled="props.selectedSectionID === null || loadingPages || creatingPage"
        @click="addPage"
      >
        <Icon :src="pageEditorIcon" class="h-4 w-4 shrink-0" />
        <span>添加页</span>
      </button>
    </header>

    <div
      class="workspace-scroll mr-1 min-h-0 flex-1 overflow-y-auto px-3 pb-3"
      :aria-busy="loadingPages"
    >
      <p v-if="pageError" role="alert" class="mb-2 text-xs text-red-600">
        {{ pageError }}
      </p>
      <p v-else-if="loadingPages" class="mb-2 text-xs text-slate-500">
        正在加载页面…
      </p>

      <template v-if="props.selectedSectionID !== null">
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
