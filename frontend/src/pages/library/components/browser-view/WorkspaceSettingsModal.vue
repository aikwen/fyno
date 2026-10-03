<script setup>
import {
  nextTick,
  onBeforeUnmount,
  ref,
  watch,
} from 'vue'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },

  workspaceDirectory: {
    type: String,
    default: '',
  },

  workspaceInitialized: {
    type: Boolean,
    default: false,
  },

  directories: {
    type: Array,
    default: () => [],
  },

  searching: {
    type: Boolean,
    default: false,
  },

  saving: {
    type: Boolean,
    default: false,
  },

  saveStatus: {
    type: String,
    default: 'idle',
  },

  saveMessage: {
    type: String,
    default: '',
  },

  reloading: {
    type: Boolean,
    default: false,
  },

  rebuilding: {
    type: Boolean,
    default: false,
  },

  maintenanceStatus: {
    type: String,
    default: 'idle',
  },

  maintenanceMessage: {
    type: String,
    default: '',
  },
})

const emit = defineEmits([
  'close',
  'search-directory',
  'save-directory',
  'directory-change',
  'reload',
  'rebuild',
])

const inputRef = ref(null)

const directory = ref('')
const dropdownOpen = ref(false)
const inputFocused = ref(false)

let searchTimer = null

const normalizeDirectory = (value) => {
  return (value ?? '').trim()
}

const scheduleSearch = (value) => {
  clearTimeout(searchTimer)

  const query =
    normalizeDirectory(value)

  if (!query) {
    dropdownOpen.value = false
    return
  }

  dropdownOpen.value = true

  searchTimer = setTimeout(() => {
    emit(
      'search-directory',
      query,
    )
  }, 200)
}

const handleInput = () => {
  emit('directory-change')

  scheduleSearch(
    directory.value,
  )
}

const handleFocus = () => {
  inputFocused.value = true

  const value =
    normalizeDirectory(
      directory.value,
    )

  if (value) {
    dropdownOpen.value = true
  }
}

const handleBlur = () => {
  inputFocused.value = false
  dropdownOpen.value = false
}

const selectDirectory = (item) => {
  directory.value = item.path
  emit('directory-change')

  nextTick(() => {
    inputRef.value?.focus()
  })
}

const saveDirectory = () => {
  const value =
    normalizeDirectory(
      directory.value,
    )

  if (
    !value
    || props.saving
  ) {
    return
  }

  dropdownOpen.value = false

  emit(
    'save-directory',
    value,
  )
}

const close = () => {
  if (
    props.saving
    || props.reloading
    || props.rebuilding
  ) {
    return
  }

  dropdownOpen.value = false
  inputFocused.value = false

  emit('close')
}

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      dropdownOpen.value = false
      inputFocused.value = false
      return
    }

    directory.value =
      props.workspaceDirectory ?? ''

    await nextTick()

    inputRef.value?.focus()
  },
)

watch(
  () => props.workspaceDirectory,
  (value) => {
    if (!props.open) {
      return
    }

    directory.value = value ?? ''
  },
)

onBeforeUnmount(() => {
  clearTimeout(searchTimer)
})
</script>

<template>
  <dialog
    class="modal"
    :open="open"
  >
    <div
      class="
        modal-box
        max-w-2xl
      "
    >
      <!-- Header -->
      <div>
        <h3
          class="
            text-lg
            font-semibold
          "
        >
          Workspace Settings
        </h3>

        <p
          class="
            mt-1
            text-sm
            text-base-content/50
          "
        >
          Configure the local Fyno workspace.
        </p>
      </div>

      <!-- Workspace directory -->
      <section class="mt-7">
        <div>
          <h4
            class="
              text-sm
              font-semibold
              text-base-content
            "
          >
            Workspace Directory
          </h4>

          <p
            class="
              mt-1
              text-xs
              text-base-content/45
            "
          >
            The local directory used by Fyno as the current workspace.
          </p>
        </div>

        <div
          class="
            relative
            mt-4
          "
        >
          <input
            ref="inputRef"
            v-model="directory"
            type="text"
            class="
              input input-bordered
              w-full
              font-mono
              text-sm
            "
            placeholder="Workspace directory"
            autocomplete="off"
            spellcheck="false"
            :disabled="
              saving
            "
            @input="handleInput"
            @focus="handleFocus"
            @blur="handleBlur"
            @keyup.enter="
              saveDirectory
            "
            @keyup.esc="
              dropdownOpen = false
            "
          >

          <!-- Directory dropdown -->
          <div
            v-if="
              inputFocused
              && dropdownOpen
              && (
                searching
                || directories.length > 0
              )
            "
            class="
              absolute
              left-0 right-0
              top-[calc(100%+6px)]
              z-30
              overflow-hidden
              rounded-lg
              border
              border-base-content/10
              bg-base-100
              shadow-[0_8px_24px_rgba(0,0,0,0.14)]
            "
          >
            <!-- Searching -->
            <div
              v-if="searching"
              class="
                flex h-12
                items-center
                gap-3
                px-4
                text-sm
                text-base-content/50
              "
            >
              <span
                class="
                  loading
                  loading-spinner
                  loading-xs
                "
              />

              Searching directories...
            </div>

            <!-- Results -->
            <div
              v-else
              class="
                max-h-64
                overflow-y-auto
                p-1
              "
            >
              <button
                v-for="item in directories"
                :key="item.path"
                type="button"
                class="
                  flex
                  w-full min-w-0
                  cursor-pointer
                  items-center
                  rounded-md
                  px-3 py-2.5
                  text-left
                  transition-colors
                  hover:bg-base-200
                "
                @pointerdown.prevent="
                  selectDirectory(item)
                "
              >
                <div class="min-w-0">
                  <div
                    class="
                      truncate
                      text-sm
                      font-medium
                      text-base-content/85
                    "
                  >
                    {{ item.name }}
                  </div>

                  <div
                    class="
                      mt-0.5
                      truncate
                      font-mono
                      text-xs
                      text-base-content/40
                    "
                    :title="item.path"
                  >
                    {{ item.path }}
                  </div>
                </div>
              </button>
            </div>
          </div>
        </div>

        <div
          class="
            mt-3
            flex
            items-center
            justify-between
            gap-4
          "
        >
          <div
            class="
              min-h-5
              text-xs
            "
          >
            <span
              v-if="
                saveStatus === 'success'
              "
              class="
                text-xs
                text-base-content/50
              "
            >
              {{
                saveMessage
                || 'Workspace updated.'
              }}
            </span>

            <span
              v-else-if="
                saveStatus === 'error'
              "
              class="
                text-xs
                text-error
              "
            >
              {{
                saveMessage
                || 'Failed to update workspace.'
              }}
            </span>
          </div>

          <button
            type="button"
            class="
              btn btn-sm
              border-none
              bg-base-content
              text-base-100
              hover:bg-base-content/85
            "
            :disabled="
              saving
              || !normalizeDirectory(
                directory,
              )
            "
            @click="saveDirectory"
          >
            <span
              v-if="saving"
              class="
                loading
                loading-spinner
                loading-xs
              "
            />

            <span v-else>
              Apply
            </span>
          </button>
        </div>

        <div
          class="
            mt-4
            rounded-lg
            border
            border-base-content/10
            px-4 py-3
          "
        >
          <div
            class="
              text-xs
              text-base-content/40
            "
          >
            Current workspace
          </div>

          <div
            class="
              mt-1
              break-all
              font-mono
              text-sm
              text-base-content/75
            "
          >
            {{
              workspaceDirectory
              || 'Not configured'
            }}
          </div>
        </div>
      </section>

      <div
        class="
          my-7
          h-px
          bg-base-content/10
        "
      />

      <!-- Maintenance -->
      <section>
        <div>
          <h4
            class="
              text-sm
              font-semibold
              text-base-content
            "
          >
            Maintenance
          </h4>

          <p
            class="
              mt-1
              text-xs
              text-base-content/45
            "
          >
            Reload or rebuild the current workspace metadata.
          </p>
        </div>

        <div
          class="
            mt-3 min-h-5
            text-xs
          "
        >
          <span
            v-if="
              maintenanceStatus === 'success'
            "
            class="
              text-xs
              text-base-content/50
            "
          >
            {{
              maintenanceMessage
              || 'Workspace maintenance completed.'
            }}
          </span>

          <span
            v-else-if="
              maintenanceStatus === 'error'
            "
            class="
              text-xs
              text-error
            "
          >
            {{
              maintenanceMessage
              || 'Workspace maintenance failed.'
            }}
          </span>
        </div>

        <!-- Reload -->
        <div
          class="
            mt-5
            flex
            items-center
            justify-between
            gap-6
          "
        >
          <div class="min-w-0">
            <div
              class="
                text-sm
                font-medium
              "
            >
              Reload Workspace
            </div>

            <div
              class="
                mt-1
                text-xs
                text-base-content/45
              "
            >
              Reload collections and notes from disk.
            </div>
          </div>

          <button
            type="button"
            class="
              btn btn-sm
              shrink-0
            "
            :disabled="
              reloading
              || !workspaceDirectory
              || !workspaceInitialized
            "
            @click="
              emit('reload')
            "
          >
            <span
              v-if="reloading"
              class="
                loading
                loading-spinner
                loading-xs
              "
            />

            <span v-else>
              Reload
            </span>
          </button>
        </div>

        <!-- Rebuild -->
        <div
          class="
            mt-5
            flex
            items-center
            justify-between
            gap-6
          "
        >
          <div class="min-w-0">
            <div
              class="
                text-sm
                font-medium
              "
            >
              Rebuild Metadata
            </div>

            <div
              class="
                mt-1
                text-xs
                leading-relaxed
                text-base-content/45
              "
            >
              Recreate the .fyno metadata from the current workspace.
              Markdown files will not be deleted.
            </div>
          </div>

          <button
            type="button"
            class="
              btn btn-sm
              shrink-0
              border-none
              bg-[#EB5971]
              text-white
              hover:bg-[#D74C63]
              disabled:bg-base-200
              disabled:text-base-content/30
              disabled:opacity-100
              disabled:hover:bg-base-200
            "
            :disabled="
              rebuilding
              || !workspaceDirectory
            "
            @click="
              emit('rebuild')
            "
          >
            <span
              v-if="rebuilding"
              class="
                loading
                loading-spinner
                loading-xs
              "
            />

            <span v-else>
              Rebuild
            </span>
          </button>
        </div>
      </section>

      <!-- Footer -->
      <div
        class="
          modal-action
          mt-8
        "
      >
        <button
          type="button"
          class="btn"
          :disabled="
            saving
            || reloading
            || rebuilding
          "
          @click="close"
        >
          Close
        </button>
      </div>
    </div>

    <div
      class="modal-backdrop"
      @click="close"
    />
  </dialog>
</template>
