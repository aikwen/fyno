<script setup>
import {
  onBeforeUnmount,
  ref,
} from 'vue'

import FileView from './components/file-view/FileView.vue'
import BrowserView from './components/browser-view/BrowserView.vue'

const activeFile = ref(null)
const fileViewReady = ref(false)

let fileViewReadyTimer = null

const clearFileViewReadyTimer = () => {
  if (fileViewReadyTimer === null) {
    return
  }

  clearTimeout(fileViewReadyTimer)
  fileViewReadyTimer = null
}

const revealFileView = () => {
  clearFileViewReadyTimer()

  if (activeFile.value) {
    fileViewReady.value = true
  }
}

const showFile = (file) => {
  if (
    activeFile.value
    && fileViewReady.value
  ) {
    activeFile.value = file
    return
  }

  activeFile.value = file
  fileViewReady.value = false

  clearFileViewReadyTimer()
  fileViewReadyTimer = setTimeout(
    revealFileView,
    1050,
  )
}

const closeFile = () => {
  clearFileViewReadyTimer()
  fileViewReady.value = false
  activeFile.value = null
}

const handleBrowserTransitionEnd = (
  event,
) => {
  if (
    event.target !== event.currentTarget
    || event.propertyName !== 'width'
    || !activeFile.value
  ) {
    return
  }

  revealFileView()
}

onBeforeUnmount(() => {
  clearFileViewReadyTimer()
})
</script>

<template>
  <section
    class="
      flex h-full min-h-0
      overflow-hidden
      bg-base-100
    "
  >
    <!-- Browser -->
    <div
      class="
        relative z-20
        h-full min-h-0
        shrink-0
        overflow-visible
        transition-[width]
        duration-1000
        ease-in-out
      "
      :style="{
        width: activeFile
          ? '360px'
          : '100%',
      }"
      @transitionend="
        handleBrowserTransitionEnd
      "
    >
      <BrowserView
        :compact="Boolean(activeFile)"
        :active-file="activeFile"
        @open-file="showFile"
        @close-file="closeFile"
      />
    </div>

    <!-- File -->
    <Transition name="file-view">
      <div
        v-if="
          activeFile
          && fileViewReady
        "
        class="
          relative z-0
          h-full min-h-0 min-w-0
          flex-1
          overflow-hidden
          border-l border-base-300/70
        "
      >
        <FileView
          :file="activeFile"
          @close="closeFile"
        />
      </div>
    </Transition>
  </section>
</template>

<style scoped>
.file-view-enter-active,
.file-view-leave-active {
  transition: opacity 220ms ease-out;
}

.file-view-enter-from,
.file-view-leave-to {
  opacity: 0;
}
</style>
