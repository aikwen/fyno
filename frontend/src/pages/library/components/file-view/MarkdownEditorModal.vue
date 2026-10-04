<script setup>
import {
  onBeforeUnmount,
  ref,
  useId,
  watch,
} from 'vue'

import {
  allToolbar,
  MdEditor,
} from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import './markdown.css'

import { updateFileContent } from '@/api/library'

import EmojiToolbar from './EmojiToolbar.vue'

const AUTOSAVE_DELAY = 600

const props = defineProps({
  file: {
    type: Object,
    required: true,
  },

  content: {
    type: String,
    default: '',
  },
})

const emit = defineEmits([
  'close',
  'update-content',
])

const editorContent = ref(props.content)
const saveStatus = ref('saved')
const saving = ref(false)
const dirty = ref(false)
const closing = ref(false)

const editorId =
  `file-model-${useId()}`

/*
 * 阅读视图与编辑模态框会同时渲染同一份 Markdown。
 * 给模态框标题加独立前缀，避免目录通过 document 查询时
 * 命中背后阅读视图中同名、同 id 的标题。
 */
const getEditorHeadingId = ({ index }) => {
  return `${editorId}-heading-${index}`
}

const editorToolbars = [
  ...allToolbar,
]

const imageToolbarIndex =
  editorToolbars.indexOf('image')

editorToolbars.splice(
  imageToolbarIndex + 1,
  0,
  0,
)

let debounceTimer = null
let savePromise = null

const clearDebounce = () => {
  if (debounceTimer === null) {
    return
  }

  window.clearTimeout(debounceTimer)
  debounceTimer = null
}

const isCurrentFile = (
  collectionId,
  fileId,
) => {
  return (
    props.file.collectionId === collectionId
    && props.file.fileId === fileId
  )
}

/*
 * 保存始终串行执行。请求期间产生的新输入只标记 dirty，
 * 当前请求结束后再用最新正文继续保存。
 */
const savePendingContent = async () => {
  if (saving.value) {
    return savePromise
  }

  if (!dirty.value) {
    return true
  }

  clearDebounce()

  const collectionId =
    props.file.collectionId
  const fileId = props.file.fileId
  const content = editorContent.value

  saving.value = true
  dirty.value = false
  saveStatus.value = 'saving'

  const currentSave = (async () => {
    let succeeded = false

    try {
      const response =
        await updateFileContent({
          collectionId,
          fileId,
          content,
        })

      if (!isCurrentFile(
        collectionId,
        fileId,
      )) {
        return false
      }

      emit(
        'update-content',
        response.content,
      )

      succeeded = true
    } catch {
      if (isCurrentFile(
        collectionId,
        fileId,
      )) {
        dirty.value = true
        saveStatus.value = 'error'
      }
    } finally {
      saving.value = false
    }

    if (!succeeded) {
      return false
    }

    if (dirty.value) {
      return savePendingContent()
    }

    saveStatus.value = 'saved'
    return true
  })()

  savePromise = currentSave

  const result = await currentSave

  if (savePromise === currentSave) {
    savePromise = null
  }

  return result
}

const scheduleSave = () => {
  clearDebounce()
  saveStatus.value = 'saving'

  debounceTimer = window.setTimeout(
    () => {
      debounceTimer = null
      void savePendingContent()
    },
    AUTOSAVE_DELAY,
  )
}

watch(editorContent, () => {
  dirty.value = true
  scheduleSave()
}, {
  flush: 'sync',
})

const closeEditor = async () => {
  if (closing.value) {
    return
  }

  clearDebounce()
  closing.value = true

  let saved = true

  if (
    saving.value
    && savePromise
  ) {
    saved = await savePromise
  }

  if (dirty.value) {
    saved = await savePendingContent()
  }

  if (
    saved
    && !saving.value
    && !dirty.value
  ) {
    emit('close')
    return
  }

  closing.value = false
  saveStatus.value = 'error'
}

onBeforeUnmount(() => {
  clearDebounce()
})
</script>

<template>
  <Teleport to="body">
    <dialog
      class="modal"
      open
      @cancel.prevent
    >
      <div
        class="
          modal-box
          flex h-[88vh]
          max-h-[88vh]
          w-[90vw]
          max-w-none
          flex-col
          overflow-hidden
          bg-base-100
          p-0
        "
      >
        <header
          class="
            flex h-14 shrink-0
            items-center justify-between
            gap-4
            border-b border-base-content/10
            px-5
          "
        >
          <div
            class="
              min-w-0 truncate
              text-sm font-medium
              text-base-content
            "
            :title="file.name"
          >
            {{ file.name }}
          </div>

          <div
            class="
              flex shrink-0
              items-center gap-4
            "
          >
            <div
              class="
                flex items-center gap-2
                text-xs
                text-base-content/60
              "
            >
              <span
                v-if="saveStatus === 'saved'"
                class="status status-success"
              />
              <span
                v-else-if="
                  saveStatus === 'saving'
                "
                class="status status-warning"
              />
              <span
                v-else
                class="status status-error"
              />

              <span v-if="saveStatus === 'saved'">
                已保存
              </span>
              <span
                v-else-if="
                  saveStatus === 'saving'
                "
              >
                保存中...
              </span>
              <span v-else>
                保存失败
              </span>
            </div>

            <button
              type="button"
              class="
                flex size-8
                cursor-pointer
                items-center justify-center
                rounded-md
                text-xl font-light
                text-base-content/60
                transition-colors
                hover:bg-base-content/5
                hover:text-base-content
                disabled:cursor-wait
                disabled:opacity-40
              "
              :disabled="closing"
              title="Close"
              aria-label="Close editor"
              @click="closeEditor"
            >
              ×
            </button>
          </div>
        </header>

        <div
          class="
            flex min-h-0 min-w-0
            flex-1 overflow-hidden
          "
        >
          <MdEditor
            v-model="editorContent"
            :id="editorId"
            :md-heading-id="getEditorHeadingId"
            class="fyno-markdown-editor"
            :preview="true"
            :scroll-auto="true"
            :no-upload-img="true"
            :footers="[]"
            :toolbars="editorToolbars"
            :toolbars-exclude="[
              'save',
              'preview',
              'previewOnly',
              'htmlPreview',
              'pageFullscreen',
              'fullscreen',
              'github',
            ]"
            :disabled="closing"
            theme="light"
            preview-theme="vuepress"
            catalog-layout="flat"
          >
            <template #defToolbars>
              <EmojiToolbar />
            </template>
          </MdEditor>
        </div>
      </div>
    </dialog>
  </Teleport>
</template>

<style scoped>
.fyno-markdown-editor {
  height: 100%;
  max-width: 100%;
  border: 0;
  border-radius: 0;
}

.fyno-markdown-editor :deep(.md-editor-content) {
  min-width: 0;
}
</style>
