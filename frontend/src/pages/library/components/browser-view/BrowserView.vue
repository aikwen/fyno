<script setup>
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  toRef,
  watch,
} from 'vue'

import { VueDraggable } from 'vue-draggable-plus'

import CollectionActions from './CollectionActions.vue'
import CollectionCard from './CollectionCard.vue'
import CollectionFilter from './CollectionFilter.vue'
import CreateCollectionModal from './CreateCollectionModal.vue'
import CreateFileModal from './CreateFileModal.vue'
import WorkspaceSettingsModal from './WorkspaceSettingsModal.vue'
import { useCollectionDrag } from './browser-view-composable/useCollectionDrag'
import { useCollectionPagination } from './browser-view-composable/useCollectionPagination'
import { useCollections } from './browser-view-composable/useCollections'
import { useFiles } from './browser-view-composable/useFiles'
import { useWorkspace } from './browser-view-composable/useWorkspace'
import { browserViewState } from './state'

const props = defineProps({
  compact: {
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
  'close-file',
])

const scrollRef = ref(null)

/*
 * 保留 activeFile 的响应性后再注入 composable，
 * 避免拆分后只捕获 setup 时的初始 prop 值。
 */
const activeFile = toRef(
  props,
  'activeFile',
)

/* Pagination 只依赖共享 state、DOM ref 与纯 normalize helper。 */
const pagination = useCollectionPagination({
  browserViewState,
  scrollRef,
})

const {
  sentinelRef,
  isSentinelVisible,
  loadMore,
  reloadCollections,
  resetCollections,
  createObserver,
  disconnectObserver,
} = pagination

const {
  createModalOpen,
  creatingCollection,
  filterOpen,
  deleteTarget,
  deletingCollection,
  findCollection,
  renameCollectionHandler,
  createCollectionHandler,
  confirmCreateCollection,
  closeCreateCollection,
  filterCollectionHandler,
  closeCollectionFilter,
  applyCollectionFilter,
  resetCollectionFilter,
  deleteCollectionHandler,
  closeDeleteCollection,
  confirmDeleteCollection,
} = useCollections({
  browserViewState,
  scrollRef,
  reloadCollections,
  loadMore,
  isSentinelVisible,
  activeFile,
  emit,
})

const {
  createFileTarget,
  createFileModalOpen,
  creatingFile,
  deleteFileTarget,
  deletingFile,
  openFileHandler,
  createFileHandler,
  confirmCreateFile,
  closeCreateFile,
  renameFileHandler,
  deleteFileHandler,
  closeDeleteFile,
  confirmDeleteFile,
  moveFileHandler,
} = useFiles({
  findCollection,
  activeFile,
  emit,
})

const syncWorkspaceLibrary = async (
  workspace,
) => {
  disconnectObserver()
  resetCollections()

  if (!workspace.initialized) {
    return
  }

  await loadMore()

  await nextTick()

  createObserver()
}

const {
  settingsModalOpen,
  workspaceDirectory,
  workspaceInitialized,
  directoryResults,
  searchingDirectory,
  savingDirectory,
  directorySaveStatus,
  directorySaveMessage,
  reloadingWorkspace,
  rebuildingWorkspace,
  maintenanceStatus,
  maintenanceMessage,
  loadWorkspace,
  openWorkspaceSettings,
  closeWorkspaceSettings,
  searchDirectory,
  saveWorkspaceDirectory,
  resetDirectorySaveStatus,
  reloadWorkspace,
  rebuildWorkspace,
} = useWorkspace({
  onWorkspaceChanged:
    syncWorkspaceLibrary,
})

const libraryReady = computed(
  () => workspaceInitialized.value,
)

const {
  handleDragStart,
  stopDragScroll,
  handleDragEnd,
} = useCollectionDrag({
  browserViewState,
  scrollRef,
})

watch(
  () =>
    browserViewState.editMode,

  async (editMode) => {
    if (editMode) {
      return
    }

    stopDragScroll()

    await nextTick()

    if (
      browserViewState.hasMore
      && isSentinelVisible()
    ) {
      await loadMore()
    }
  },
)

onMounted(async () => {
  try {
    await loadWorkspace()
  } catch (error) {
    console.error(
      'Failed to initialize workspace:',
      error,
    )
    return
  }

  if (!workspaceInitialized.value) {
    return
  }

  /* Workspace 恢复完成后，再加载 Collection 并观察 sentinel。 */
  await loadMore()

  createObserver()
})

onBeforeUnmount(() => {
  /* Observer 与拖拽监听由组装层在同一生命周期统一释放。 */
  disconnectObserver()

  stopDragScroll()
})
</script>

<template>
  <section
    class="
      relative
      h-full min-h-0
      overflow-visible
    "
  >
    <div
      ref="scrollRef"
      class="
        browser-view-scrollbar
        h-full
        overflow-x-hidden
        overflow-y-auto
      "
    >
      <div
        class="
          mx-auto
          w-full max-w-5xl
          px-6 py-4
        "
      >
        <VueDraggable
          v-model="
            browserViewState.collections
          "
          handle=".drag-handle"
          :disabled="
            !browserViewState.editMode
          "
          :animation="180"
          :scroll="false"
          ghost-class="collection-ghost"
          class="
            flex flex-col gap-4
          "
          @start="handleDragStart"
          @end="handleDragEnd"
        >
          <CollectionCard
            v-for="
              collection
              in browserViewState.collections
            "
            :key="
              collection.collectionId
            "
            :collection="collection"
            :edit-mode="
              browserViewState.editMode
            "
            :active-file="
              activeFile
            "
            @open-file="
              openFileHandler
            "
            @rename="
              renameCollectionHandler
            "
            @delete="
              deleteCollectionHandler
            "
            @create-file="
              createFileHandler
            "
            @rename-file="
              renameFileHandler
            "
            @delete-file="
              deleteFileHandler
            "
            @move-file="
              moveFileHandler
            "
          />
        </VueDraggable>

        <div
          ref="sentinelRef"
          class="h-px w-full"
        />

        <div
          v-if="
            !browserViewState.loading
            && !browserViewState.hasMore
            && browserViewState.collections.length === 0
          "
          class="
            py-16
            text-center
            text-sm
            text-base-content/40
          "
        >
          No collections
        </div>
      </div>
    </div>

    <CollectionFilter
      :open="filterOpen"
      :keywords="
        browserViewState.filters.keywords
      "
      :compact="compact"
      @apply="
        applyCollectionFilter
      "
      @close="
        closeCollectionFilter
      "
    />

    <CollectionActions
      :filter-open="filterOpen"
      :library-ready="libraryReady"
      @create="
        createCollectionHandler
      "
      @filter="
        filterCollectionHandler
      "
      @reset-filter="
        resetCollectionFilter
      "
      @settings="
        openWorkspaceSettings
      "
    />

    <WorkspaceSettingsModal
      :open="settingsModalOpen"
      :workspace-directory="workspaceDirectory"
      :workspace-initialized="
        workspaceInitialized
      "
      :directories="directoryResults"
      :searching="searchingDirectory"
      :saving="savingDirectory"
      :save-status="directorySaveStatus"
      :save-message="directorySaveMessage"
      :reloading="reloadingWorkspace"
      :rebuilding="rebuildingWorkspace"
      :maintenance-status="maintenanceStatus"
      :maintenance-message="maintenanceMessage"
      @close="closeWorkspaceSettings"
      @search-directory="searchDirectory"
      @save-directory="saveWorkspaceDirectory"
      @directory-change="resetDirectorySaveStatus"
      @reload="reloadWorkspace"
      @rebuild="rebuildWorkspace"
    />

    <CreateCollectionModal
      :open="createModalOpen"
      :loading="
        creatingCollection
      "
      @close="
        closeCreateCollection
      "
      @confirm="
        confirmCreateCollection
      "
    />

    <CreateFileModal
      :open="
        createFileModalOpen
      "
      :loading="
        creatingFile
      "
      @close="
        closeCreateFile
      "
      @confirm="
        confirmCreateFile
      "
    />

    <!-- File delete confirmation -->
    <dialog
      class="modal"
      :open="
        Boolean(deleteFileTarget)
      "
    >
      <div class="modal-box">
        <h3
          class="
            text-lg font-semibold
          "
        >
          Delete Note
        </h3>

        <p
          class="
            mt-4
            text-sm
            text-base-content/65
          "
        >
          Delete
          <span
            class="
              font-medium
              text-base-content
            "
          >
            {{ deleteFileTarget?.name }}
          </span>
          ?
        </p>

        <p
          class="
            mt-2
            text-xs
            text-base-content/45
          "
        >
          This action cannot be undone.
        </p>

        <div class="modal-action">
          <button
            type="button"
            class="btn"
            :disabled="
              deletingFile
            "
            @click="
              closeDeleteFile
            "
          >
            Cancel
          </button>

          <button
            type="button"
            class="
              btn
              border-none
              bg-[#EB5971]
              text-white
              hover:bg-[#D74C63]
            "
            :disabled="
              deletingFile
            "
            @click="
              confirmDeleteFile
            "
          >
            <span
              v-if="
                deletingFile
              "
              class="
                loading
                loading-spinner
                loading-sm
              "
            />

            <span v-else>
              Delete
            </span>
          </button>
        </div>
      </div>

      <div
        class="modal-backdrop"
        @click="
          closeDeleteFile
        "
      />
    </dialog>

    <!-- Collection delete confirmation -->
    <dialog
      class="modal"
      :open="
        Boolean(deleteTarget)
      "
    >
      <div class="modal-box">
        <h3
          class="
            text-lg font-semibold
          "
        >
          Delete Collection
        </h3>

        <p
          class="
            mt-4
            text-sm
            text-base-content/65
          "
        >
          Delete
          <span
            class="
              font-medium
              text-base-content
            "
          >
            {{ deleteTarget?.name }}
          </span>
          and all notes inside it?
        </p>

        <p
          class="
            mt-2
            text-xs
            text-base-content/45
          "
        >
          This action cannot be undone.
        </p>

        <div class="modal-action">
          <button
            type="button"
            class="btn"
            :disabled="
              deletingCollection
            "
            @click="
              closeDeleteCollection
            "
          >
            Cancel
          </button>

          <button
            type="button"
            class="
              btn
              border-none
              bg-[#EB5971]
              text-white
              hover:bg-[#D74C63]
            "
            :disabled="
              deletingCollection
            "
            @click="
              confirmDeleteCollection
            "
          >
            <span
              v-if="
                deletingCollection
              "
              class="
                loading
                loading-spinner
                loading-sm
              "
            />

            <span v-else>
              Delete
            </span>
          </button>
        </div>
      </div>

      <div
        class="modal-backdrop"
        @click="
          closeDeleteCollection
        "
      />
    </dialog>
  </section>
</template>

<style scoped>
.browser-view-scrollbar {
  scrollbar-width: thin;

  scrollbar-color:
    transparent
    transparent;
}

.browser-view-scrollbar:hover {
  scrollbar-color:
    color-mix(
      in oklab,
      currentColor 16%,
      transparent
    )
    transparent;
}

.browser-view-scrollbar::-webkit-scrollbar {
  width: 2px;
}

.browser-view-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.browser-view-scrollbar::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 9999px;
}

.browser-view-scrollbar:hover::-webkit-scrollbar-thumb {
  background:
    color-mix(
      in oklab,
      currentColor 16%,
      transparent
    );
}

.browser-view-scrollbar:hover::-webkit-scrollbar-thumb:hover {
  background:
    color-mix(
      in oklab,
      currentColor 26%,
      transparent
    );
}

.browser-view-scrollbar::-webkit-scrollbar:horizontal {
  height: 0;
}

:deep(.collection-ghost) {
  opacity: 0.35;
}
</style>
