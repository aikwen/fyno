import {
  nextTick,
  ref,
} from 'vue'

import {
  createCollection,
  deleteCollection,
  renameCollection,
} from '@/api/library'

import { normalizeCollection } from './normalize'

export const useCollections = ({
  browserViewState,
  scrollRef,
  reloadCollections,
  loadMore,
  isSentinelVisible,
  activeFile,
  emit,
}) => {
  /* Collection modal、filter 与删除确认的局部 UI 状态。 */
  const createModalOpen = ref(false)
  const creatingCollection = ref(false)

  const filterOpen = ref(false)

  const deleteTarget = ref(null)
  const deletingCollection = ref(false)

  const findCollection = (collectionId) => {
    return browserViewState.collections.find(
      collection =>
        collection.collectionId
        === collectionId,
    )
  }

  const renameCollectionHandler = async ({
    collection,
    name,
  }) => {
    try {
      const updatedCollection =
        await renameCollection({
          collectionId:
            collection.collectionId,

          name,
        })

      collection.name =
        updatedCollection.name
    } catch (error) {
      console.error(
        'Failed to rename collection:',
        error,
      )
    }
  }

  const createCollectionHandler = () => {
    createModalOpen.value = true
  }

  const confirmCreateCollection = async (name) => {
    if (creatingCollection.value) {
      return
    }

    creatingCollection.value = true

    try {
      const collection =
        await createCollection({
          name,
        })

      browserViewState.collections.push(
        normalizeCollection(collection),
      )

      createModalOpen.value = false

      await nextTick()

      scrollRef.value?.scrollTo({
        top:
          scrollRef.value.scrollHeight,

        behavior:
          'smooth',
      })
    } catch (error) {
      console.error(
        'Failed to create collection:',
        error,
      )
    } finally {
      creatingCollection.value = false
    }
  }

  const closeCreateCollection = () => {
    if (creatingCollection.value) {
      return
    }

    createModalOpen.value = false
  }

  const filterCollectionHandler = (open) => {
    filterOpen.value = open
  }

  const closeCollectionFilter = () => {
    filterOpen.value = false
  }

  const applyCollectionFilter = async (
    keywords,
  ) => {
    browserViewState.filters.keywords = [
      ...keywords,
    ]

    await reloadCollections()
  }

  const resetCollectionFilter = async () => {
    filterOpen.value = false

    browserViewState.filters.keywords = []

    await reloadCollections()
  }

  const deleteCollectionHandler = (
    collection,
  ) => {
    deleteTarget.value = collection
  }

  const closeDeleteCollection = () => {
    if (deletingCollection.value) {
      return
    }

    deleteTarget.value = null
  }

  const confirmDeleteCollection = async () => {
    const collection =
      deleteTarget.value

    if (
      !collection
      || deletingCollection.value
    ) {
      return
    }

    deletingCollection.value = true

    try {
      await deleteCollection({
        collectionId:
          collection.collectionId,
      })

      const containsActiveFile =
        activeFile.value?.collectionId
        === collection.collectionId

      const index =
        browserViewState.collections.findIndex(
          item =>
            item.collectionId
            === collection.collectionId,
        )

      if (index !== -1) {
        browserViewState.collections.splice(
          index,
          1,
        )
      }

      if (containsActiveFile) {
        /* 删除包含当前文件的 Collection 时同步关闭 FileView。 */
        emit('close-file')
      }

      deleteTarget.value = null

      await nextTick()

      if (
        browserViewState.hasMore
        && isSentinelVisible()
      ) {
        /* 删除后如果 viewport 仍未填满，沿用分页逻辑继续补齐。 */
        await loadMore()
      }
    } catch (error) {
      console.error(
        'Failed to delete collection:',
        error,
      )
    } finally {
      deletingCollection.value = false
    }
  }

  return {
    createModalOpen,
    creatingCollection,
    filterOpen,
    deleteTarget,
    deletingCollection,
    findCollection,
    renameCollectionHandler,
    createCollectionHandler,
    confirmCreateCollection,
    closeCreateCollection,
    filterCollectionHandler,
    closeCollectionFilter,
    applyCollectionFilter,
    resetCollectionFilter,
    deleteCollectionHandler,
    closeDeleteCollection,
    confirmDeleteCollection,
  }
}
