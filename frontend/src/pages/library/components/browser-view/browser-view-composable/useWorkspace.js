import { ref } from 'vue'

import {
  getWorkspace,
  rebuildWorkspace as rebuildWorkspaceApi,
  reloadWorkspace as reloadWorkspaceApi,
  searchDirectories,
  updateWorkspace,
} from '@/api/workspace'

export const useWorkspace = ({
  onWorkspaceChanged,
}) => {
  /* Modal 可见性与后端当前实际生效的 Workspace。 */
  const settingsModalOpen = ref(false)

  const workspaceDirectory = ref('')
  const workspaceInitialized = ref(false)
  const directoryResults = ref([])

  const searchingDirectory = ref(false)
  const savingDirectory = ref(false)
  const directorySaveStatus = ref('idle')
  const directorySaveMessage = ref('')
  const reloadingWorkspace = ref(false)
  const rebuildingWorkspace = ref(false)
  const maintenanceStatus = ref('idle')
  const maintenanceMessage = ref('')

  /*
   * 每次搜索递增版本号，较慢返回的旧请求不得覆盖最新输入结果。
   */
  let directoryQueryVersion = 0

  const resetMaintenanceStatus = () => {
    maintenanceStatus.value = 'idle'
    maintenanceMessage.value = ''
  }

  const loadWorkspace = async () => {
    const workspace =
      await getWorkspace()

    workspaceDirectory.value =
      workspace.directory

    workspaceInitialized.value =
      Boolean(workspace.initialized)

    return workspace
  }

  const openWorkspaceSettings = async () => {
    directoryQueryVersion += 1
    directoryResults.value = []
    searchingDirectory.value = false
    directorySaveStatus.value = 'idle'
    directorySaveMessage.value = ''
    resetMaintenanceStatus()

    try {
      await loadWorkspace()

      settingsModalOpen.value = true
    } catch (error) {
      console.error(
        'Failed to load workspace settings:',
        error,
      )
    }
  }

  const closeWorkspaceSettings = () => {
    if (
      savingDirectory.value
      || reloadingWorkspace.value
      || rebuildingWorkspace.value
    ) {
      return
    }

    directoryQueryVersion += 1

    settingsModalOpen.value = false
    directoryResults.value = []
    searchingDirectory.value = false
    resetMaintenanceStatus()
  }

  const searchDirectory = async (path) => {
    const queryVersion =
      ++directoryQueryVersion

    searchingDirectory.value = true

    try {
      const directories =
        await searchDirectories({
          path,
          limit: 20,
        })

      if (
        queryVersion
        !== directoryQueryVersion
      ) {
        return
      }

      directoryResults.value =
        directories
    } catch (error) {
      if (
        queryVersion
        === directoryQueryVersion
      ) {
        console.error(
          'Failed to search directories:',
          error,
        )

        directoryResults.value = []
      }
    } finally {
      if (
        queryVersion
        === directoryQueryVersion
      ) {
        searchingDirectory.value = false
      }
    }
  }

  const saveWorkspaceDirectory = async (path) => {
    if (savingDirectory.value) {
      return
    }

    savingDirectory.value = true
    directorySaveStatus.value = 'idle'
    directorySaveMessage.value = ''

    try {
      const workspace =
        await updateWorkspace({
          directory: path,
        })

      workspaceDirectory.value =
        workspace.directory

      workspaceInitialized.value =
        Boolean(workspace.initialized)

      await onWorkspaceChanged(
        workspace,
      )

      directorySaveStatus.value =
        'success'

      directorySaveMessage.value =
        'Workspace updated.'

      resetMaintenanceStatus()
    } catch (error) {
      directorySaveStatus.value =
        'error'

      directorySaveMessage.value =
        error?.data?.detail
        ?? 'Failed to update workspace.'
    } finally {
      savingDirectory.value = false
    }
  }

  const resetDirectorySaveStatus = () => {
    directorySaveStatus.value = 'idle'
    directorySaveMessage.value = ''
  }

  const reloadWorkspace = async () => {
    if (!workspaceDirectory.value) {
      maintenanceStatus.value = 'error'
      maintenanceMessage.value =
        'Workspace is not configured.'
      return
    }

    if (reloadingWorkspace.value) {
      return
    }

    reloadingWorkspace.value = true
    maintenanceStatus.value = 'idle'
    maintenanceMessage.value = ''

    try {
      await reloadWorkspaceApi()

      const workspace =
        await loadWorkspace()

      await onWorkspaceChanged(
        workspace,
      )

      maintenanceStatus.value = 'success'
      maintenanceMessage.value =
        'Workspace reloaded.'
    } catch (error) {
      maintenanceStatus.value = 'error'
      maintenanceMessage.value =
        error?.data?.detail
        ?? 'Failed to reload workspace.'
    } finally {
      reloadingWorkspace.value = false
    }
  }

  const rebuildWorkspace = async () => {
    if (!workspaceDirectory.value) {
      maintenanceStatus.value = 'error'
      maintenanceMessage.value =
        'Workspace is not configured.'
      return
    }

    if (rebuildingWorkspace.value) {
      return
    }

    rebuildingWorkspace.value = true
    maintenanceStatus.value = 'idle'
    maintenanceMessage.value = ''

    try {
      await rebuildWorkspaceApi()

      const workspace =
        await loadWorkspace()

      await onWorkspaceChanged(
        workspace,
      )

      maintenanceStatus.value = 'success'
      maintenanceMessage.value =
        'Workspace metadata rebuilt.'
    } catch (error) {
      maintenanceStatus.value = 'error'
      maintenanceMessage.value =
        error?.data?.detail
        ?? 'Failed to rebuild workspace.'
    } finally {
      rebuildingWorkspace.value = false
    }
  }

  return {
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
  }
}
