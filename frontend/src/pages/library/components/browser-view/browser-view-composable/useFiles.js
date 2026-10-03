import { ref } from 'vue'

import {
  createFile,
  deleteFile,
  moveFile,
  renameFile,
} from '@/api/library'

import {
  isSameFile,
  normalizeFile,
} from './normalize'

export const useFiles = ({
  findCollection,
  activeFile,
  emit,
}) => {
  /* Create/Delete modal 状态只属于 File 交互，不进入共享 state。 */
  const createFileTarget = ref(null)
  const createFileModalOpen = ref(false)
  const creatingFile = ref(false)

  const deleteFileTarget = ref(null)
  const deletingFile = ref(false)

  const openFileHandler = (file) => {
    emit('open-file', file)
  }

  const createFileHandler = ({
    collection,
  }) => {
    createFileTarget.value = collection
    createFileModalOpen.value = true
  }

  const confirmCreateFile = async (name) => {
    const collection =
      createFileTarget.value

    if (
      !collection
      || creatingFile.value
    ) {
      return
    }

    creatingFile.value = true

    try {
      const file =
        await createFile({
          collectionId:
            collection.collectionId,
          name,
        })

      collection.files.push(file)

      collection.fileCount += 1

      createFileModalOpen.value = false
      createFileTarget.value = null
    } catch (error) {
      console.error(
        'Failed to create file:',
        error,
      )
    } finally {
      creatingFile.value = false
    }
  }

  const closeCreateFile = () => {
    if (creatingFile.value) {
      return
    }

    createFileModalOpen.value = false
    createFileTarget.value = null
  }

  const renameFileHandler = async ({
    file,
    name,
  }) => {
    const collection =
      findCollection(file.collectionId)

    if (!collection) {
      return
    }

    const targetFile =
      collection.files.find(
        item =>
          item.fileId === file.fileId,
      )

    if (!targetFile) {
      return
    }

    try {
      const updatedFile =
        await renameFile({
          collectionId:
            file.collectionId,

          fileId:
            file.fileId,

          name,
        })

      targetFile.name =
        updatedFile.name

      if (
        isSameFile(
          activeFile.value,
          file,
        )
      ) {
        /* 当前打开文件被重命名时，同步 FileView 持有的数据。 */
        emit(
          'open-file',
          normalizeFile(
            collection,
            updatedFile,
          ),
        )
      }
    } catch (error) {
      console.error(
        'Failed to rename file:',
        error,
      )
    }
  }

  const deleteFileHandler = (file) => {
    deleteFileTarget.value = file
  }

  const closeDeleteFile = () => {
    if (deletingFile.value) {
      return
    }

    deleteFileTarget.value = null
  }

  const confirmDeleteFile = async () => {
    const file =
      deleteFileTarget.value

    if (
      !file
      || deletingFile.value
    ) {
      return
    }

    const collection =
      findCollection(file.collectionId)

    if (!collection) {
      deleteFileTarget.value = null
      return
    }

    const index =
      collection.files.findIndex(
        item =>
          item.fileId === file.fileId,
      )

    if (index === -1) {
      deleteFileTarget.value = null
      return
    }

    const deletingActiveFile =
      isSameFile(
        activeFile.value,
        file,
      )

    /*
     * 删除当前文件时：
     * 1. 优先下一个
     * 2. 没有下一个则上一个
     * 3. 都没有则关闭 FileView
     */
    const nextFile =
      deletingActiveFile
        ? (
            collection.files[index + 1]
            ?? collection.files[index - 1]
            ?? null
          )
        : null

    deletingFile.value = true

    try {
      await deleteFile({
        collectionId:
          file.collectionId,

        fileId:
          file.fileId,
      })

      collection.files.splice(
        index,
        1,
      )

      collection.fileCount =
        Math.max(
          0,
          collection.fileCount - 1,
        )

      deleteFileTarget.value = null

      if (!deletingActiveFile) {
        return
      }

      if (nextFile) {
        emit(
          'open-file',
          normalizeFile(
            collection,
            nextFile,
          ),
        )
      } else {
        emit('close-file')
      }
    } catch (error) {
      console.error(
        'Failed to delete file:',
        error,
      )
    } finally {
      deletingFile.value = false
    }
  }

  const moveFileHandler = async ({
    collectionId,
    file,
    afterFileId,
    oldIndex,
    newIndex,
  }) => {
    const collection =
      findCollection(collectionId)

    if (!collection) {
      return
    }

    try {
      await moveFile({
        collectionId,

        fileId:
          file.fileId,

        afterFileId,
      })
    } catch (error) {
      console.error(
        'Failed to move file:',
        error,
      )

      const movedFile =
        collection.files[newIndex]

      if (!movedFile) {
        return
      }

      collection.files.splice(
        newIndex,
        1,
      )

      collection.files.splice(
        oldIndex,
        0,
        movedFile,
      )
    }
  }

  return {
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
  }
}
