<script setup>
import { appState } from '../state/app.js'
</script>

<template>
  <main class="min-h-full px-8 py-10">
    <section class="mx-auto max-w-5xl rounded-3xl border border-white/70 bg-white/80 p-10 shadow-xl shadow-slate-300/30 backdrop-blur">
      <p class="text-sm font-semibold tracking-[0.25em] text-slate-500 uppercase">Fyno</p>
      <h1 class="mt-3 text-3xl font-bold tracking-tight text-slate-900">Fyno Workspace</h1>

      <div class="mt-8 rounded-2xl bg-slate-100 px-5 py-4">
        <p class="text-xs font-semibold tracking-wide text-slate-500 uppercase">当前工作目录</p>
        <p class="mt-2 break-all text-sm text-slate-800">{{ appState.rootDir }}</p>
      </div>

      <p
        v-if="appState.error"
        role="status"
        class="mt-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"
      >
        {{ appState.error }}
      </p>

      <div class="mt-10 border-t border-slate-200 pt-8 text-slate-500">
        Library 工作区将在后续版本中接入。
      </div>
    </section>
  </main>
</template>
