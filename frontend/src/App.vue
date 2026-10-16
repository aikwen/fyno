<script setup>
import { onMounted } from 'vue'
import { appState, initialize } from './state/app.js'
import WelcomeView from './views/WelcomeView.vue'
import WorkspaceView from './views/WorkspaceView.vue'

onMounted(initialize)
</script>

<template>
  <main
    v-if="appState.view === 'loading'"
    class="flex min-h-full items-center justify-center px-6 text-sm font-medium text-slate-600"
  >
    正在加载 Fyno…
  </main>
  <WelcomeView v-else-if="appState.view === 'welcome'" />
  <WorkspaceView v-else />
</template>
