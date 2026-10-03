<script setup>
import Icon from './Icon.vue'

const items = [
  {
    name: 'Library',
    icon: 'library',
    to: '/library',
  },
  {
    name: 'Settings',
    icon: 'settings',
    to: '/settings',
  },
]
</script>

<template>
  <aside
    class="
      relative z-30
      flex h-screen w-14 shrink-0 flex-col items-center
      overflow-visible
      bg-base-200
      py-2
    "
  >
    <nav class="flex flex-col items-center gap-2.5">
      <div
        v-for="item in items"
        :key="item.to"
        class="tooltip tooltip-right"
        :data-tip="item.name"
      >
        <RouterLink
          :to="item.to"
          custom
          v-slot="{ href, navigate, isActive }"
        >
          <a
            :href="href"
            class="
              flex size-9 items-center justify-center
              rounded-xl
              transition-colors
              hover:bg-[rgb(236,236,236)]
              hover:text-neutral-950
            "
            :class="
              isActive
                ? 'bg-[rgb(236,236,236)] text-neutral-950'
                : 'text-neutral-500'
            "
            @click="navigate"
          >
            <Icon
              :name="item.icon"
              class="size-5"
            />
          </a>
        </RouterLink>
      </div>
    </nav>
  </aside>
</template>
