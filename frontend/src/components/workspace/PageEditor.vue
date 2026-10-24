<script setup>
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { Editor, EditorContent } from '@tiptap/vue-3'
import Highlight from '@tiptap/extension-highlight'
import Placeholder from '@tiptap/extension-placeholder'
import TaskItem from '@tiptap/extension-task-item'
import TaskList from '@tiptap/extension-task-list'
import StarterKit from '@tiptap/starter-kit'
import { pageApi } from '../../api/page.js'
import EditorToolbar from './editor/EditorToolbar.vue'
import '../../assets/styles/editor.css'

const props = defineProps({
  selectedPageID: {
    type: Number,
    default: null,
  },
  warning: {
    type: String,
    default: '',
  },
})

const SAVE_DELAY = 1500
const EMPTY_DOCUMENT = { type: 'doc', content: [{ type: 'paragraph' }] }

const editor = shallowRef(null)
const page = ref(null)
const loading = ref(false)
const loadError = ref('')
const saveState = ref('saved')
const saveError = ref('')
const sessions = new Map()

let activeSession = null
let loadRequest = 0
let applyingContent = false
let stopped = false

const saveLabel = computed(() => ({
  saved: '已保存',
  pending: '待保存',
  saving: '保存中',
  error: '保存失败',
})[saveState.value])

function describeError(action, error) {
  const message = error instanceof Error ? error.message : String(error ?? '')
  return message ? `${action}失败：${message}` : `${action}失败，请稍后重试`
}

function isDocument(content) {
  return content !== null &&
    typeof content === 'object' &&
    !Array.isArray(content) &&
    content.type === 'doc' &&
    (content.content === undefined || Array.isArray(content.content))
}

function cloneDocument(content) {
  return JSON.parse(JSON.stringify(content))
}

function normalizeDocument(content) {
  if (
    content.type === 'doc' &&
    (content.content === undefined || content.content.length === 0)
  ) {
    return {
      type: 'doc',
      content: [{ type: 'paragraph' }],
    }
  }

  return content
}

function isActive(session) {
  return activeSession === session && props.selectedPageID === session.pageID
}

function showSessionState(session) {
  if (!isActive(session)) {
    return
  }

  saveError.value = session.error
  if (session.error) {
    saveState.value = 'error'
  } else if (session.saving) {
    saveState.value = 'saving'
  } else if (session.savedRevision < session.revision) {
    saveState.value = 'pending'
  } else {
    saveState.value = 'saved'
  }
}

function queueSave(session) {
  if (!session || session.savedRevision >= session.revision) {
    return session?.saveChain ?? Promise.resolve()
  }

  const revision = session.revision
  if (session.enqueuedRevision >= revision) {
    return session.saveChain
  }

  const content = cloneDocument(session.content)
  session.enqueuedRevision = revision

  const save = async () => {
    session.saving = true
    session.error = ''
    showSessionState(session)
    try {
      await pageApi.saveContent(session.pageID, content)
      session.savedRevision = Math.max(session.savedRevision, revision)
      session.error = ''
    } catch (error) {
      session.error = describeError('保存正文', error)
      if (session.enqueuedRevision === revision) {
        session.enqueuedRevision = session.savedRevision
      }
    } finally {
      session.saving = false
      showSessionState(session)
    }
  }

  session.saveChain = session.saveChain.then(save, save)
  return session.saveChain
}

function scheduleSave(session) {
  clearTimeout(session.timer)
  session.timer = window.setTimeout(() => {
    session.timer = null
    void queueSave(session)
  }, SAVE_DELAY)
}

function flushSession(session) {
  if (!session) {
    return Promise.resolve()
  }

  clearTimeout(session.timer)
  session.timer = null
  return queueSave(session)
}

function handleEditorUpdate({ editor: currentEditor }) {
  if (applyingContent || !activeSession || !isActive(activeSession)) {
    return
  }

  activeSession.content = currentEditor.getJSON()
  activeSession.revision += 1
  activeSession.error = ''
  showSessionState(activeSession)
  scheduleSave(activeSession)
}

function createSession(pageID, metadata, content) {
  return {
    pageID,
    page: metadata,
    content: cloneDocument(content),
    revision: 0,
    savedRevision: 0,
    enqueuedRevision: 0,
    saving: false,
    error: '',
    timer: null,
    saveChain: Promise.resolve(),
  }
}

function applySession(session) {
  applyingContent = true
  try {
    editor.value.commands.setContent(session.content, {
      emitUpdate: false,
      errorOnInvalidContent: true,
    })
  } finally {
    applyingContent = false
  }

  activeSession = session
  page.value = session.page
  editor.value.setEditable(true, false)
  showSessionState(session)
}

async function loadPage(pageID) {
  const request = ++loadRequest
  const previousSession = activeSession

  activeSession = null
  editor.value?.setEditable(false, false)
  loading.value = pageID !== null
  loadError.value = ''
  saveError.value = ''
  page.value = null

  void flushSession(previousSession)

  if (pageID === null) {
    loading.value = false
    saveState.value = 'saved'
    return
  }

  try {
    const cachedBeforeLoad = sessions.get(pageID)
    if (cachedBeforeLoad && (
      cachedBeforeLoad.saving ||
      cachedBeforeLoad.savedRevision < cachedBeforeLoad.revision
    )) {
      await flushSession(cachedBeforeLoad)
      if (request !== loadRequest || props.selectedPageID !== pageID || stopped) {
        return
      }
    }

    const result = await pageApi.get(pageID)
    if (request !== loadRequest || props.selectedPageID !== pageID || stopped) {
      return
    }

    if (!result?.page || result.page.id !== pageID || !isDocument(result.content)) {
      throw new Error('返回的页面正文不是有效的 Tiptap JSON')
    }

    const loadedContent = normalizeDocument(result.content)
    const cachedSession = sessions.get(pageID)
    const hasUnsavedContent = cachedSession &&
      cachedSession.savedRevision < cachedSession.revision
    const session = hasUnsavedContent
      ? cachedSession
      : createSession(pageID, result.page, loadedContent)

    session.page = result.page
    sessions.set(pageID, session)
    applySession(session)
  } catch (error) {
    if (request === loadRequest && props.selectedPageID === pageID && !stopped) {
      loadError.value = describeError('加载正文', error)
    }
  } finally {
    if (request === loadRequest && !stopped) {
      loading.value = false
    }
  }
}

function retrySave() {
  if (!activeSession || saveState.value !== 'error') {
    return
  }

  activeSession.error = ''
  showSessionState(activeSession)
  void queueSave(activeSession)
}

onMounted(() => {
  editor.value = new Editor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
        link: {
          openOnClick: false,
          autolink: true,
          linkOnPaste: true,
        },
      }),
      TaskList,
      TaskItem.configure({ nested: true }),
      Highlight,
      Placeholder.configure({ placeholder: '开始输入正文…' }),
    ],
    content: EMPTY_DOCUMENT,
    editable: false,
    editorProps: {
      attributes: {
        class: 'fyno-page-content',
        'aria-label': '页面正文',
      },
    },
    onUpdate: handleEditorUpdate,
  })

  void loadPage(props.selectedPageID)
})

watch(
  () => props.selectedPageID,
  (pageID) => {
    if (editor.value) {
      void loadPage(pageID)
    }
  },
)

onBeforeUnmount(() => {
  stopped = true
  loadRequest += 1
  for (const session of sessions.values()) {
    clearTimeout(session.timer)
    session.timer = null
  }
  void flushSession(activeSession)
  activeSession = null
  editor.value?.destroy()
  editor.value = null
})
</script>

<template>
  <section class="workspace-scroll min-w-0 flex-1 overflow-y-auto bg-white">
    <div class="mx-auto min-h-full w-full max-w-4xl px-14 pb-16 pt-8">
      <p
        v-if="warning"
        role="status"
        class="mb-4 text-sm text-amber-700"
      >
        {{ warning }}
      </p>

      <div
        v-if="selectedPageID === null"
        class="flex min-h-[60vh] items-center justify-center text-sm text-slate-400"
      >
        选择一个页面开始编辑
      </div>

      <template v-else>
        <div class="flex min-h-14 items-end justify-between gap-6 border-b border-slate-300 px-4 pb-2">
          <h1 class="min-w-0 truncate text-3xl font-normal text-slate-900">
            {{ page?.title || (loading ? '正在加载…' : '页面') }}
          </h1>

          <button
            v-if="page"
            type="button"
            class="mb-1 inline-flex shrink-0 items-center gap-1.5 text-xs transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-300/70"
            :class="saveState === 'error' ? 'cursor-pointer text-red-600 hover:text-red-700' : 'cursor-default text-slate-400'"
            :disabled="saveState !== 'error'"
            :title="saveState === 'error' ? `${saveError}，点击重试` : saveLabel"
            @click="retrySave"
          >
            <span
              aria-hidden="true"
              class="h-2 w-2 rounded-full"
              :class="{
                'bg-emerald-400': saveState === 'saved',
                'bg-amber-400': saveState === 'pending',
                'animate-pulse bg-violet-400': saveState === 'saving',
                'bg-red-500': saveState === 'error',
              }"
            />
            {{ saveLabel }}
          </button>
        </div>

        <EditorToolbar
          :editor="editor"
          :disabled="loading || !page || Boolean(loadError)"
        />

        <p v-if="loading" role="status" class="px-4 py-6 text-sm text-slate-500">
          正在加载正文…
        </p>
        <div v-else-if="loadError" role="alert" class="mx-4 mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {{ loadError }}
        </div>
        <div v-else-if="page" class="px-4 pt-6">
          <p v-if="saveState === 'error'" role="alert" class="mb-3 text-xs text-red-600">
            {{ saveError }}；正文仍保留在当前编辑器中，可继续编辑或点击右上角重试。
          </p>
          <EditorContent :editor="editor" />
        </div>
      </template>
    </div>
  </section>
</template>
