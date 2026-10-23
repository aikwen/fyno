<script setup>
import { ref } from 'vue'
import { appState } from '../state/app.js'
import Sidebar from '../components/workspace/Sidebar.vue'
import PageList from '../components/workspace/PageList.vue'
import PageEditor from '../components/workspace/PageEditor.vue'

const sidebarExpanded = ref(true)
const selectedNotebookID = ref(null)
const selectedSectionID = ref(null)
const selectedPageID = ref(null)

function selectNotebook(notebookID) {
  if (selectedNotebookID.value === notebookID) {
    return
  }

  selectedNotebookID.value = notebookID
  selectedSectionID.value = null
  selectedPageID.value = null
}

function selectSection({ notebookID, sectionID }) {
  selectedNotebookID.value = notebookID

  if (selectedSectionID.value === sectionID) {
    return
  }

  selectedSectionID.value = sectionID
  selectedPageID.value = null
}

function deleteNotebook(notebookID) {
  if (selectedNotebookID.value !== notebookID) {
    return
  }

  selectedNotebookID.value = null
  selectedSectionID.value = null
  selectedPageID.value = null
}

function deleteSection({ notebookID, sectionID }) {
  if (selectedSectionID.value !== sectionID) {
    return
  }

  selectedNotebookID.value = notebookID
  selectedSectionID.value = null
  selectedPageID.value = null
}

function deletePage(pageID) {
  if (selectedPageID.value === pageID) {
    selectedPageID.value = null
  }
}
</script>

<template>
  <main class="flex h-full min-h-0 w-full overflow-hidden bg-white">
    <Sidebar
      :expanded="sidebarExpanded"
      :selected-notebook-i-d="selectedNotebookID"
      :selected-section-i-d="selectedSectionID"
      @toggle="sidebarExpanded = !sidebarExpanded"
      @select-notebook="selectNotebook"
      @select-section="selectSection"
      @delete-notebook="deleteNotebook"
      @delete-section="deleteSection"
    />
    <div class="flex min-w-0 flex-1 bg-white">
      <PageList
        :selected-page-i-d="selectedPageID"
        :selected-section-i-d="selectedSectionID"
        @select-page="selectedPageID = $event"
        @delete-page="deletePage"
      />
      <PageEditor :selected-page-i-d="selectedPageID" :warning="appState.error" />
    </div>
  </main>
</template>
