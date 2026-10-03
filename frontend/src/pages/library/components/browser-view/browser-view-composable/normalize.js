export const normalizeCollection = (collection) => {
  return {
    ...collection,

    expanded: false,
    loaded: false,
    loading: false,
    files: [],
  }
}

export const normalizeFile = (
  collection,
  file,
) => {
  return {
    ...file,

    collectionId:
      collection.collectionId,

    collectionName:
      collection.name,
  }
}

export const isSameFile = (
  a,
  b,
) => {
  return Boolean(
    a
    && b
    && a.collectionId === b.collectionId
    && a.fileId === b.fileId
  )
}
