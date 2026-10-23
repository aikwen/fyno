<script setup>
import { getCurrentInstance, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  open: {
    type: Boolean,
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
  message: {
    type: String,
    required: true,
  },
  confirmText: {
    type: String,
    default: '确定',
  },
  cancelText: {
    type: String,
    default: '取消',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['confirm', 'cancel'])
const dialog = ref(null)
const cancelButton = ref(null)
const instanceID = getCurrentInstance()?.uid ?? 0
const titleID = `confirm-dialog-title-${instanceID}`
const descriptionID = `confirm-dialog-description-${instanceID}`
let previousFocus = null

function cancel() {
  if (!props.loading) {
    emit('cancel')
  }
}

function confirm() {
  if (!props.loading) {
    emit('confirm')
  }
}

function focusableElements() {
  if (!dialog.value) {
    return []
  }

  return [...dialog.value.querySelectorAll(
    'button:not(:disabled), [href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])',
  )]
}

function handleKeyDown(event) {
  if (!props.open) {
    return
  }

  if (event.key === 'Escape') {
    if (!props.loading) {
      event.preventDefault()
      emit('cancel')
    }
    return
  }

  if (event.key !== 'Tab') {
    return
  }

  const elements = focusableElements()
  if (elements.length === 0) {
    event.preventDefault()
    dialog.value?.focus()
    return
  }

  const first = elements[0]
  const last = elements[elements.length - 1]
  if (document.activeElement === dialog.value || !dialog.value?.contains(document.activeElement)) {
    event.preventDefault()
    const target = event.shiftKey ? last : first
    target.focus()
  } else if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

function restoreFocus() {
  if (previousFocus instanceof HTMLElement && document.contains(previousFocus)) {
    previousFocus.focus()
  }
  previousFocus = null
}

watch(
  () => props.open,
  async (open) => {
    if (open) {
      previousFocus = document.activeElement
      await nextTick()
      cancelButton.value?.focus()
    } else {
      restoreFocus()
    }
  },
)

onMounted(() => {
  document.addEventListener('keydown', handleKeyDown)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeyDown)
  restoreFocus()
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/35 p-6"
      @click.self="cancel"
    >
      <div
        ref="dialog"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleID"
        :aria-describedby="descriptionID"
        tabindex="-1"
        class="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-5 text-slate-800 shadow-xl"
      >
        <h2 :id="titleID" class="text-base font-semibold text-slate-900">
          {{ title }}
        </h2>
        <p :id="descriptionID" class="mt-2 text-sm leading-6 text-slate-600">
          {{ message }}
        </p>
        <p v-if="error" role="alert" class="mt-3 text-sm text-red-600">
          {{ error }}
        </p>

        <div class="mt-5 flex justify-end gap-2">
          <button
            ref="cancelButton"
            type="button"
            class="h-8 rounded-md border border-slate-300 bg-white px-4 text-sm text-slate-700 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400/60 disabled:cursor-default disabled:opacity-50"
            :disabled="loading"
            @click="cancel"
          >
            {{ cancelText }}
          </button>
          <button
            type="button"
            class="h-8 rounded-md bg-red-600 px-4 text-sm font-medium text-white hover:bg-red-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-400/70 disabled:cursor-default disabled:opacity-60"
            :disabled="loading"
            @click="confirm"
          >
            {{ loading ? '删除中…' : confirmText }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
