<script setup>
import {
  nextTick,
  onBeforeUnmount,
  ref,
  watch,
} from 'vue'

import deleteIcon from '@/assets/delete.svg'
import dragHandleIcon from '@/assets/drag-handle.svg'
import editIcon from '@/assets/edit.svg'
import ellipsisIcon from '@/assets/ellipsis.svg'

const props = defineProps({
  file: {
    type: Object,
    required: true,
  },

  active: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'open',
  'rename',
  'delete',
])

const itemRef = ref(null)
const renameInputRef = ref(null)
const menuButtonRef = ref(null)
const menuRef = ref(null)

const renaming = ref(false)
const draftName = ref('')

const menuOpen = ref(false)
const menuLeft = ref(0)
const menuTop = ref(0)

const openFile = () => {
  if (renaming.value) {
    return
  }

  emit('open', props.file)
}

const closeMenu = () => {
  menuOpen.value = false
}

const startRename = async () => {
  closeMenu()

  draftName.value = props.file.name
  renaming.value = true

  await nextTick()

  renameInputRef.value?.focus()
  renameInputRef.value?.select()
}

const cancelRename = () => {
  renaming.value = false
  draftName.value = ''
}

const confirmRename = () => {
  if (!renaming.value) {
    return
  }

  const name = draftName.value.trim()

  if (!name) {
    cancelRename()
    return
  }

  if (name !== props.file.name) {
    emit('rename', {
      file: props.file,
      name,
    })
  }

  renaming.value = false
  draftName.value = ''
}

const deleteFile = () => {
  if (renaming.value) {
    return
  }

  emit('delete', props.file)
}

const positionMenu = async () => {
  await nextTick()

  const button = menuButtonRef.value
  const menu = menuRef.value

  if (
    !button
    || !menu
    || !menuOpen.value
  ) {
    return
  }

  const buttonRect =
    button.getBoundingClientRect()

  const menuRect =
    menu.getBoundingClientRect()

  const gap = 6
  const viewportPadding = 8

  let left =
    buttonRect.right - menuRect.width

  let top =
    buttonRect.bottom + gap

  if (
    top + menuRect.height
    > window.innerHeight - viewportPadding
  ) {
    top =
      buttonRect.top
      - menuRect.height
      - gap
  }

  menuLeft.value = Math.min(
    Math.max(
      viewportPadding,
      left,
    ),
    Math.max(
      viewportPadding,
      window.innerWidth
        - menuRect.width
        - viewportPadding,
    ),
  )

  menuTop.value = Math.min(
    Math.max(
      viewportPadding,
      top,
    ),
    Math.max(
      viewportPadding,
      window.innerHeight
        - menuRect.height
        - viewportPadding,
    ),
  )
}

const toggleMenu = async () => {
  if (renaming.value) {
    return
  }

  menuOpen.value = !menuOpen.value

  if (menuOpen.value) {
    await positionMenu()
  }
}

const renameFromMenu = () => {
  startRename()
}

const deleteFromMenu = () => {
  closeMenu()
  deleteFile()
}

const handleMenuPointerDown = (event) => {
  const button = menuButtonRef.value
  const menu = menuRef.value

  if (
    !button?.contains(event.target)
    && !menu?.contains(event.target)
  ) {
    closeMenu()
  }
}

const handleRenamePointerDown = (event) => {
  const item = itemRef.value

  if (!item) {
    return
  }

  if (!item.contains(event.target)) {
    confirmRename()
  }
}

const handleMenuKeydown = (event) => {
  if (event.key !== 'Escape') {
    return
  }

  event.preventDefault()
  event.stopPropagation()

  closeMenu()
}

const addMenuListeners = () => {
  document.addEventListener(
    'pointerdown',
    handleMenuPointerDown,
  )

  document.addEventListener(
    'keydown',
    handleMenuKeydown,
  )

  window.addEventListener(
    'resize',
    closeMenu,
  )

  window.addEventListener(
    'scroll',
    closeMenu,
    true,
  )
}

const removeMenuListeners = () => {
  document.removeEventListener(
    'pointerdown',
    handleMenuPointerDown,
  )

  document.removeEventListener(
    'keydown',
    handleMenuKeydown,
  )

  window.removeEventListener(
    'resize',
    closeMenu,
  )

  window.removeEventListener(
    'scroll',
    closeMenu,
    true,
  )
}

const addRenameListeners = () => {
  document.addEventListener(
    'pointerdown',
    handleRenamePointerDown,
  )
}

const removeRenameListeners = () => {
  document.removeEventListener(
    'pointerdown',
    handleRenamePointerDown,
  )
}

watch(
  menuOpen,
  (open) => {
    if (open) {
      addMenuListeners()
      return
    }

    removeMenuListeners()
  },
)

watch(
  renaming,
  (active) => {
    if (active) {
      addRenameListeners()
      return
    }

    removeRenameListeners()
  },
)

onBeforeUnmount(() => {
  removeMenuListeners()
  removeRenameListeners()
})
</script>

<template>
  <div
    ref="itemRef"
    class="
      group/file
      flex min-w-0
      cursor-pointer
      items-center
      rounded-md
      px-2 py-2
      text-sm
      transition-colors
    "
    :class="
      active
        ? 'bg-[#005BAC] text-white'
        : 'text-base-content/80 hover:bg-base-200/70'
    "
  >
    <!-- Drag handle -->
    <div
      class="
        file-drag-handle
        mr-1
        flex size-6 shrink-0
        cursor-grab
        items-center justify-center
        rounded
        opacity-0
        transition-opacity
        group-hover/file:opacity-100
        active:cursor-grabbing
      "
      title="Drag"
      @click.stop
    >
      <img
        :src="dragHandleIcon"
        alt=""
        class="size-4"
        :class="
          active
            ? 'brightness-0 invert opacity-90'
            : 'opacity-55'
        "
      >
    </div>

    <!-- File content -->
    <div
      class="
        min-w-0 flex-1
        cursor-pointer
      "
      @click="openFile"
    >
      <input
        v-if="renaming"
        ref="renameInputRef"
        v-model="draftName"
        type="text"
        class="
          input input-sm
          h-8 w-full
          min-w-0
          cursor-text
          bg-base-100
          text-base-content
        "
        @click.stop
        @dblclick.stop
        @keyup.enter="confirmRename"
        @keyup.esc="cancelRename"
      >

      <span
        v-else
        class="
          block
          w-fit max-w-full
          cursor-pointer
          truncate
        "
        :title="file.name"
      >
        {{ file.name }}
      </span>
    </div>

    <!-- File menu trigger -->
    <button
      v-if="!renaming"
      ref="menuButtonRef"
      type="button"
      class="
        file-menu-button
        ml-1
        flex size-7 shrink-0
        cursor-pointer
        items-center justify-center
        rounded
        transition
      "
      :class="[
        menuOpen
          ? 'opacity-100 pointer-events-auto'
          : 'opacity-0 pointer-events-none group-hover/file:opacity-100 group-hover/file:pointer-events-auto',

        active
          ? 'hover:bg-white/15'
          : 'hover:bg-base-300/60',
      ]"
      title="More actions"
      aria-label="File actions"
      aria-haspopup="menu"
      :aria-expanded="menuOpen"
      @click.stop="toggleMenu"
      @dblclick.stop
    >
      <img
        :src="ellipsisIcon"
        alt=""
        class="
          file-menu-trigger-icon
          size-4
          transition
        "
        :class="
          active
            ? 'brightness-0 invert opacity-90'
            : 'opacity-60'
        "
      >
    </button>
  </div>

  <Teleport to="body">
    <div
      v-if="menuOpen"
      ref="menuRef"
      role="menu"
      class="
        fixed
        z-[200]
        w-36
        rounded-lg
        border
        border-base-content/10
        bg-base-100
        p-1
        shadow-[0_8px_24px_rgba(0,0,0,0.16)]
      "
      :style="{
        left: `${menuLeft}px`,
        top: `${menuTop}px`,
      }"
      @pointerdown.stop
      @click.stop
    >
      <button
        type="button"
        role="menuitem"
        class="
          flex h-9 w-full
          cursor-pointer
          items-center
          gap-2.5
          rounded-md
          px-3
          text-left
          text-sm
          text-base-content/75
          hover:bg-base-200
        "
        @click="renameFromMenu"
      >
        <img
          :src="editIcon"
          alt=""
          class="
            size-4
            opacity-65
          "
        >

        <span>
          Rename
        </span>
      </button>

      <button
        type="button"
        role="menuitem"
        class="
          file-menu-delete
          flex h-9 w-full
          cursor-pointer
          items-center
          gap-2.5
          rounded-md
          px-3
          text-left
          text-sm
          text-error/80
          hover:bg-error/10
        "
        @click="deleteFromMenu"
      >
        <img
          :src="deleteIcon"
          alt=""
          class="
            file-menu-delete-icon
            size-4
            opacity-65
          "
        >

        <span>
          Delete
        </span>
      </button>
    </div>
  </Teleport>
</template>

<style scoped>
.file-menu-delete:hover
.file-menu-delete-icon {
  filter:
    invert(48%)
    sepia(70%)
    saturate(1800%)
    hue-rotate(313deg)
    brightness(97%)
    contrast(90%);

  opacity: 1;
}
</style>
