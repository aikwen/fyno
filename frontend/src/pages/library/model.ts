export interface FileMeta {
  collectionId: string
  fileId: string
  name: string
}

export interface CollectionMeta {
  collectionId: string
  name: string
  fileCount: number
}

export const isSameFile = (
  a?: FileMeta | null,
  b?: FileMeta | null,
) => {
  return a?.collectionId === b?.collectionId
    && a?.fileId === b?.fileId
}