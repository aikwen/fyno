import { createRouter, createWebHistory } from 'vue-router'

import Library from '../pages/library/Library.vue'
import Settings from '../pages/Settings.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/library',
    },
    {
      path: '/library',
      name: 'library',
      component: Library,
    },
    {
      path: '/settings',
      name: 'settings',
      component: Settings,
    },
  ],
})

export default router