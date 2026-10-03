<script setup>
import { ref } from 'vue'

import FileView from './components/file-view/FileView.vue'
import BrowserView from './components/browser-view/BrowserView.vue'

const activeFile = ref(null)

const showFile = (file) => {
  activeFile.value = file
}

const closeFile = () => {
  activeFile.value = null
}
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
        duration-500
        ease-in-out
      "
      :style="{
        width: activeFile
          ? '360px'
          : '100%',
      }"
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
        v-if="activeFile"
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
  transition:
    opacity 320ms ease,
    transform 420ms ease;
}

.file-view-enter-from,
.file-view-leave-to {
  opacity: 0;
  transform: translateX(12px);
}
</style>
