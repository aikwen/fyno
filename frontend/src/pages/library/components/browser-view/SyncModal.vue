<script setup>
import {
  computed,
  onBeforeUnmount,
  ref,
  watch,
} from 'vue'

import closeIcon from '@/assets/close.svg'
import { config } from '@/config'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'close',
])

const socket = ref(null)
const connected = ref(false)
const connecting = ref(false)
const refreshing = ref(false)
const syncing = ref(false)
const info = ref(null)
const result = ref(null)
const remote = ref('')
const errorMessage = ref('')

let sessionVersion = 0

const changes = computed(() => {
  return info.value?.changes ?? []
})

const busy = computed(() => {
  return (
    connecting.value
    || refreshing.value
    || syncing.value
  )
})

const statusLabel = computed(() => {
  if (connecting.value && !info.value) {
    return 'Connecting...'
  }

  if (!info.value) {
    return 'Waiting for sync status'
  }

  if (!info.value.git_available) {
    return 'Git is not available'
  }

  if (!info.value.repository) {
    return 'Ready to initialize'
  }

  if (changes.value.length > 0) {
    const suffix =
      changes.value.length === 1
        ? 'change'
        : 'changes'

    return `${changes.value.length} ${suffix}`
  }

  if (info.value.synced) {
    return 'Up to date'
  }

  return 'Pending sync'
})

const statusClass = computed(() => {
  if (
    info.value
    && !info.value.git_available
  ) {
    return 'text-error'
  }

  if (info.value?.synced) {
    return 'text-success'
  }

  return 'text-base-content'
})

const resultMessage = computed(() => {
  if (!result.value) {
    return ''
  }

  if (result.value.status === 'success') {
    return 'Synced successfully'
  }

  if (result.value.status === 'clean') {
    return 'Already up to date'
  }

  return result.value.reason || 'Sync failed'
})

const resultClass = computed(() => {
  return result.value?.status === 'error'
    ? 'text-error'
    : 'text-success'
})

const websocketUrl = () => {
  const url = new URL(
    config.apiBaseUrl,
    window.location.href,
  )

  url.protocol =
    url.protocol === 'https:'
      ? 'wss:'
      : 'ws:'
  url.pathname = '/library/sync/ws'
  url.search = ''
  url.hash = ''

  return url.toString()
}

const disposeSocket = () => {
  sessionVersion += 1

  const currentSocket = socket.value

  socket.value = null
  connected.value = false
  connecting.value = false
  refreshing.value = false
  syncing.value = false

  if (!currentSocket) {
    return
  }

  currentSocket.onopen = null
  currentSocket.onmessage = null
  currentSocket.onerror = null
  currentSocket.onclose = null

  if (
    currentSocket.readyState
      === WebSocket.CONNECTING
    || currentSocket.readyState
      === WebSocket.OPEN
  ) {
    try {
      currentSocket.close()
    } catch {
      // Closing is best-effort when the browser is still establishing a socket.
    }
  }
}

const resetSession = () => {
  info.value = null
  result.value = null
  remote.value = ''
  errorMessage.value = ''
}

const handleMessage = (message) => {
  if (message.type === 'info') {
    info.value = message.data
    remote.value = message.data?.remote ?? ''
    refreshing.value = false
    syncing.value = false
    return
  }

  if (message.type === 'result') {
    result.value = message.data
    return
  }

  if (message.type === 'error') {
    errorMessage.value =
      message.reason
      || 'Sync service returned an error.'
    refreshing.value = false
    syncing.value = false
  }
}

const connect = () => {
  disposeSocket()
  resetSession()
  connecting.value = true

  const currentSession = sessionVersion
  let currentSocket

  try {
    currentSocket = new WebSocket(
      websocketUrl(),
    )
  } catch {
    connecting.value = false
    errorMessage.value =
      'Unable to connect to Sync service.'
    return
  }

  socket.value = currentSocket

  currentSocket.onopen = () => {
    if (currentSession !== sessionVersion) {
      return
    }

    connected.value = true
    connecting.value = false
    errorMessage.value = ''
  }

  currentSocket.onmessage = (event) => {
    if (currentSession !== sessionVersion) {
      return
    }

    try {
      handleMessage(
        JSON.parse(event.data),
      )
    } catch {
      errorMessage.value =
        'Sync service returned an invalid response.'
      refreshing.value = false
      syncing.value = false
    }
  }

  currentSocket.onerror = () => {
    if (currentSession !== sessionVersion) {
      return
    }

    connecting.value = false
    refreshing.value = false
    syncing.value = false
    errorMessage.value =
      'Unable to connect to Sync service.'
  }

  currentSocket.onclose = () => {
    if (currentSession !== sessionVersion) {
      return
    }

    socket.value = null
    connected.value = false
    connecting.value = false
    refreshing.value = false
    syncing.value = false

    if (!errorMessage.value) {
      errorMessage.value =
        'Connection to Sync service was closed.'
    }
  }
}

const sendMessage = (message) => {
  const currentSocket = socket.value

  if (
    !currentSocket
    || currentSocket.readyState
      !== WebSocket.OPEN
  ) {
    errorMessage.value =
      'Unable to connect to Sync service.'
    return false
  }

  try {
    currentSocket.send(
      JSON.stringify(message),
    )
    return true
  } catch {
    errorMessage.value =
      'Unable to send request to Sync service.'
    return false
  }
}

const refresh = () => {
  if (busy.value || !connected.value) {
    return
  }

  errorMessage.value = ''
  result.value = null
  refreshing.value = true

  if (!sendMessage({ action: 'refresh' })) {
    refreshing.value = false
  }
}

const sync = () => {
  if (
    busy.value
    || !connected.value
    || info.value?.git_available === false
  ) {
    return
  }

  errorMessage.value = ''
  result.value = null
  syncing.value = true

  if (!sendMessage({
    action: 'sync',
    remote: remote.value,
  })) {
    syncing.value = false
  }
}

const close = () => {
  disposeSocket()
  emit('close')
}

watch(
  () => props.open,
  (open) => {
    if (open) {
      connect()
      return
    }

    disposeSocket()
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  disposeSocket()
})
</script>

<template>
  <dialog
    class="modal"
    :open="open"
  >
    <div class="modal-box max-w-2xl">
      <div
        class="
          flex items-center
          justify-between gap-4
        "
      >
        <h3 class="text-lg font-semibold">
          Sync
        </h3>

        <button
          type="button"
          class="btn btn-ghost btn-sm btn-circle"
          aria-label="Close Sync"
          @click="close"
        >
          <img
            :src="closeIcon"
            alt=""
            class="size-4 opacity-70"
          >
        </button>
      </div>

      <div class="mt-5">
        <label
          for="sync-remote"
          class="text-sm font-medium"
        >
          Remote repository
        </label>

        <input
          id="sync-remote"
          v-model="remote"
          type="text"
          class="input input-bordered mt-2 w-full"
          placeholder="git@github.com:user/repository.git"
          :disabled="busy"
          @keyup.esc="close"
        >

        <p
          v-if="info && info.remote === null"
          class="mt-2 text-xs text-base-content/55"
        >
          A remote repository is required for the first sync.
        </p>
      </div>

      <div
        class="
          mt-5 rounded-box
          bg-base-200/60 p-4
        "
      >
        <p
          class="
            text-xs font-medium
            uppercase tracking-wide
            text-base-content/50
          "
        >
          Status
        </p>

        <div
          class="mt-2 flex items-center gap-2"
        >
          <span
            v-if="busy"
            class="loading loading-spinner loading-sm"
          />

          <p
            class="text-sm font-medium"
            :class="statusClass"
          >
            {{ statusLabel }}
          </p>
        </div>

        <p
          v-if="info && !info.repository && info.git_available"
          class="mt-2 text-xs text-base-content/55"
        >
          Git repository will be initialized on first sync.
        </p>

        <p
          v-if="info && !info.success && info.reason"
          class="mt-3 whitespace-pre-wrap break-words text-sm text-error"
        >
          {{ info.reason }}
        </p>
      </div>

      <div class="mt-5">
        <p class="text-sm font-medium">
          Changes
        </p>

        <div
          class="
            sync-changes-scrollbar
            mt-2 max-h-48
            overflow-y-auto
            rounded-box
            bg-base-100 p-3
          "
        >
          <ul
            v-if="changes.length > 0"
            class="space-y-1"
          >
            <li
              v-for="change in changes"
              :key="change"
              class="
                whitespace-pre-wrap
                break-all font-mono
                text-sm
              "
            >
              {{ change }}
            </li>
          </ul>

          <p
            v-else
            class="text-sm text-base-content/45"
          >
            No local file changes.
          </p>
        </div>
      </div>

      <p
        v-if="resultMessage"
        class="mt-4 whitespace-pre-wrap break-words text-sm"
        :class="resultClass"
      >
        {{ resultMessage }}
      </p>

      <p
        v-if="errorMessage"
        class="mt-4 whitespace-pre-wrap break-words text-sm text-error"
      >
        {{ errorMessage }}
      </p>

      <div class="modal-action">
        <button
          type="button"
          class="btn"
          :disabled="busy || !connected"
          @click="refresh"
        >
          <span
            v-if="refreshing"
            class="loading loading-spinner loading-sm"
          />

          <span>Refresh</span>
        </button>

        <button
          type="button"
          class="
            btn
            border-none
            bg-[#005BAC]
            text-white
            hover:bg-[#004C91]
          "
          :disabled="
            busy
            || !connected
            || info?.git_available === false
          "
          @click="sync"
        >
          <span
            v-if="syncing"
            class="loading loading-spinner loading-sm"
          />

          <span>Sync</span>
        </button>
      </div>
    </div>

    <div
      class="modal-backdrop"
      @click="close"
    />
  </dialog>
</template>

<style scoped>
.sync-changes-scrollbar {
  scrollbar-color:
    color-mix(
      in oklab,
      currentColor 18%,
      transparent
    )
    transparent;
  scrollbar-width: thin;
}

.sync-changes-scrollbar::-webkit-scrollbar {
  width: 2px;
}

.sync-changes-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.sync-changes-scrollbar::-webkit-scrollbar-thumb {
  background:
    color-mix(
      in oklab,
      currentColor 18%,
      transparent
    );
  border-radius: 9999px;
}
</style>
