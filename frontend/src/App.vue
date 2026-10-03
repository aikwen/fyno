<script setup>
import ToolRail from './components/ToolRail.vue'
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-base-200 text-base-content">
    <ToolRail />

    <main
      class="
        min-h-0 min-w-0 flex-1
        overflow-hidden
        rounded-l-2xl
        bg-base-100
        shadow-[-4px_0_12px_rgba(0,0,0,0.04)]
      "
    >
      <RouterView />
    </main>
  </div>
</template>