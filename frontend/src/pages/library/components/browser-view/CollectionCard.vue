<script setup>
import {
  nextTick,
  onBeforeUnmount,
  ref,
} from 'vue'

import { VueDraggable } from 'vue-draggable-plus'

import { getCollectionFiles } from '@/api/library'
import deleteIcon from '@/assets/delete.svg'
import dragIcon from '@/assets/drag.svg'
import notesIcon from '@/assets/notes.svg'

import FileItem from './FileItem.vue'

const props = defineProps({
  collection: {
    type: Object,
    required: true,
  },

  editMode: {
    type: Boolean,
    default: false,
  },

  activeFile: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits([
  'open-file',
  'rename',
  'delete',
  'create-file',
  'rename-file',
  'delete-file',
  'move-file',
])

const cardRef = ref(null)
const renameInputRef = ref(null)

const renaming = ref(false)
const draftName = ref('')

const toggleExpand = async () => {
  if (props.editMode) {
    return
  }

  if (renaming.value) {
    confirmRename()
  }

  if (props.collection.expanded) {
    props.collection.expanded = false
    return
  }

  props.collection.expanded = true

  if (
    props.collection.loaded
    || props.collection.loading
  ) {
    return
  }

  props.collection.loading = true

  try {
    props.collection.files =
      await getCollectionFiles(
        props.collection.collectionId,
      )

    props.collection.loaded = true
  } catch (error) {
    console.error(
      'Failed to load collection files:',
      error,
    )

    props.collection.expanded = false
  } finally {
    props.collection.loading = false
  }
}

const normalizeFile = (file) => {
  return {
    ...file,
    collectionId:
      props.collection.collectionId,

    collectionName:
      props.collection.name,
  }
}

const isActiveFile = (file) => {
  if (!props.activeFile) {
    return false
  }

  return (
    props.activeFile.collectionId
      === props.collection.collectionId
    && props.activeFile.fileId
      === file.fileId
  )
}

const openFile = (file) => {
  if (
    props.editMode
    || renaming.value
  ) {
    return
  }

  emit(
    'open-file',
    normalizeFile(file),
  )
}

const createFile = () => {
  if (
    props.editMode
    || renaming.value
  ) {
    return
  }

  emit('create-file', {
    collection: props.collection,
  })
}

const renameFile = ({
  file,
  name,
}) => {
  emit('rename-file', {
    file: normalizeFile(file),
    name,
  })
}

const deleteFile = (file) => {
  emit(
    'delete-file',
    normalizeFile(file),
  )
}

const handleFileDragEnd = (event) => {
  const {
    oldIndex,
    newIndex,
  } = event

  if (
    oldIndex == null
    || newIndex == null
    || oldIndex === newIndex
  ) {
    return
  }

  const movedFile =
    props.collection.files[newIndex]

  if (!movedFile) {
    return
  }

  const previousFile =
    props.collection.files[newIndex - 1]
    ?? null

  emit('move-file', {
    collectionId:
      props.collection.collectionId,

    file:
      normalizeFile(movedFile),

    afterFileId:
      previousFile?.fileId ?? null,

    oldIndex,
    newIndex,
  })
}

const startRename = async () => {
  if (props.editMode) {
    return
  }

  draftName.value =
    props.collection.name

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

  const name =
    draftName.value.trim()

  if (!name) {
    cancelRename()
    return
  }

  if (
    name
    !== props.collection.name
  ) {
    emit('rename', {
      collection: props.collection,
      name,
    })
  }

  renaming.value = false
  draftName.value = ''
}

const handleDocumentPointerDown = (
  event,
) => {
  if (!renaming.value) {
    return
  }

  const card = cardRef.value

  if (!card) {
    return
  }

  if (!card.contains(event.target)) {
    confirmRename()
  }
}

document.addEventListener(
  'pointerdown',
  handleDocumentPointerDown,
)

onBeforeUnmount(() => {
  document.removeEventListener(
    'pointerdown',
    handleDocumentPointerDown,
  )
})
</script>

<template>
  <article
    ref="cardRef"
    class="
      group relative
      overflow-hidden
      rounded-xl
      border border-[#E2E2E2]
      bg-base-100
      shadow-none
      transition-shadow
      duration-200
      hover:shadow-[0_5px_18px_rgba(0,0,0,0.08)]
    "
  >
    <div class="px-6 pt-5">
      <!-- Header -->
      <div class="min-w-0">
        <input
          v-if="renaming"
          ref="renameInputRef"
          v-model="draftName"
          type="text"
          class="
            input input-bordered
            h-10 w-full max-w-xl
            text-lg font-semibold
          "
          @keyup.enter="confirmRename"
          @keyup.esc="cancelRename"
        >

        <h3
          v-else
          class="
            truncate
            text-xl font-semibold
            tracking-tight
            text-base-content
          "
          :title="collection.name"
          @dblclick="startRename"
        >
          {{ collection.name }}
        </h3>
      </div>

      <!-- File count -->
      <div
        class="
          mt-5
          flex items-center gap-2
          text-sm text-base-content/55
        "
      >
        <img
          :src="notesIcon"
          alt=""
          class="
            size-4 shrink-0
            opacity-55
          "
        >

        <span>
          {{ collection.fileCount }}
          {{
            collection.fileCount === 1
              ? 'note'
              : 'notes'
          }}
        </span>
      </div>

      <!-- Detail bar -->
      <div
        class="
          relative mt-5
          flex
          justify-center
          border-t-[3px]
          border-[#005BAC]
          pb-8
        "
      >
        <button
          type="button"
          class="
            detail-tab
            absolute
            top-[-2px]
            flex h-5
            cursor-pointer select-none
            items-center justify-center
            px-4
            text-xs font-medium
            leading-none
            text-white
            transition-colors
            hover:bg-[#004C91]
          "
          :disabled="editMode"
          @click="toggleExpand"
        >
          {{
            collection.expanded
              ? '收起详情'
              : '展开详情'
          }}
        </button>
      </div>

      <!-- Expanded content -->
      <Transition
        name="collection-details"
      >
        <div
          v-if="collection.expanded"
          class="collection-details"
        >
          <div
            class="
              min-h-0
              overflow-hidden
            "
          >
            <div class="pb-6 pt-1">
              <!-- Loading -->
              <div
                v-if="collection.loading"
                class="space-y-2"
              >
                <div
                  class="
                    skeleton
                    h-9 w-full
                    rounded-md
                  "
                />

                <div
                  class="
                    skeleton
                    h-9 w-[94%]
                    rounded-md
                  "
                />

                <div
                  class="
                    skeleton
                    h-9 w-[88%]
                    rounded-md
                  "
                />
              </div>

              <!-- Files -->
              <div
                v-else
                class="space-y-1"
              >
                <VueDraggable
                  v-model="collection.files"
                  handle=".file-drag-handle"
                  :animation="160"
                  :disabled="editMode"
                  ghost-class="file-ghost"
                  chosen-class="file-chosen"
                  drag-class="file-dragging"
                  class="space-y-1"
                  @end="handleFileDragEnd"
                >
                  <FileItem
                    v-for="
                      file in collection.files
                    "
                    :key="file.fileId"
                    :file="file"
                    :active="
                      isActiveFile(file)
                    "
                    @open="openFile"
                    @rename="renameFile"
                    @delete="deleteFile"
                  />
                </VueDraggable>

                <!-- Create file -->
                <button
                  type="button"
                  class="
                    mt-2
                    flex h-10 w-full
                    cursor-pointer
                    items-center justify-center
                    rounded-md
                    border border-dashed
                    border-base-content/25
                    text-xl
                    font-light
                    text-base-content/35
                    transition-colors
                    hover:border-[#005BAC]/70
                    hover:bg-[#005BAC]/5
                    hover:text-[#005BAC]
                  "
                  :disabled="editMode"
                  title="Create note"
                  @click="createFile"
                >
                  +
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- Edit mode overlay -->
    <div
      v-if="editMode"
      class="
        absolute inset-0
        z-10
        flex
        bg-base-100/55
        backdrop-blur-[1px]
      "
    >
      <!-- Drag area -->
      <div
        class="
          drag-handle
          flex flex-1
          cursor-grab
          items-center justify-center
          border-r
          border-base-300/70
          active:cursor-grabbing
        "
        title="Drag"
      >
        <img
          :src="dragIcon"
          alt=""
          class="
            size-7
            opacity-65
          "
        >
      </div>

      <!-- Delete area -->
      <button
        type="button"
        class="
          flex flex-1
          cursor-pointer
          items-center justify-center
          transition-colors
          hover:bg-error/10
        "
        title="Delete"
        @click="
          emit(
            'delete',
            collection,
          )
        "
      >
        <img
          :src="deleteIcon"
          alt=""
          class="
            size-7
            opacity-70
            transition
            group-hover:opacity-100
          "
        >
      </button>
    </div>
  </article>
</template>

<style scoped>
.collection-details {
  display: grid;
  grid-template-rows: 1fr;
}

.collection-details-enter-active,
.collection-details-leave-active {
  transition:
    grid-template-rows 200ms ease-out,
    opacity 200ms ease-out;
}

.collection-details-enter-from,
.collection-details-leave-to {
  grid-template-rows: 0fr;
  opacity: 0;
}

.detail-tab {
  background: #005bac;

  clip-path: polygon(
    0 0,
    100% 0,
    calc(100% - 16px) 100%,
    16px 100%
  );
}

:deep(.file-ghost) {
  background:
    rgba(0, 91, 172, 0.12);

  outline:
    1px dashed
    rgba(0, 91, 172, 0.55);

  opacity: 0.45;
}

:deep(.file-chosen) {
  background:
    rgba(0, 91, 172, 0.08);

  box-shadow:
    0 4px 12px
    rgba(0, 0, 0, 0.12);
}

:deep(.file-dragging) {
  background:
    var(--color-base-100);

  box-shadow:
    0 8px 20px
    rgba(0, 0, 0, 0.16);

  opacity: 0.92;
}

:deep(
  .file-chosen
  .file-drag-handle
),
:deep(
  .file-dragging
  .file-drag-handle
) {
  opacity: 1;
}
</style>
