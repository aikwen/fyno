import { api } from './client'

export const getCollections = ({
  keywords = [],
  offset = 0,
  limit = 20,
}) => {
  return api('/library/collections', {
    query: {
      keywords,
      offset,
      limit,
    },
  })
}

export const getCollectionFiles = (collectionId) => {
  return api(`/library/collections/${collectionId}/files`)
}

export const getFileContent = ({
  collectionId,
  fileId,
}) => {
  return api(
    `/library/collections/${collectionId}/files/${fileId}`,
  )
}

export const updateFileContent = ({
  collectionId,
  fileId,
  content,
}) => {
  return api(
    `/library/collections/${collectionId}/files/${fileId}`,
    {
      method: 'PUT',
      body: {
        content,
      },
    },
  )
}

export const renameCollection = ({
  collectionId,
  name,
}) => {
  return api(`/library/collections/${collectionId}`, {
    method: 'PATCH',
    body: {
      name,
    },
  })
}

export const createCollection = ({
  name,
}) => {
  return api('/library/collections', {
    method: 'POST',
    body: {
      name,
    },
  })
}

export const deleteCollection = ({
  collectionId,
}) => {
  return api(
    `/library/collections/${collectionId}`,
    {
      method: 'DELETE',
    },
  )
}

export const moveCollection = ({
  collectionId,
  afterCollectionId,
}) => {
  return api(
    `/library/collections/${collectionId}/position`,
    {
      method: 'PATCH',
      body: {
        afterCollectionId,
      },
    },
  )
}

export const createFile = ({
  collectionId,
  name,
}) => {
  return api(
    `/library/collections/${collectionId}/files`,
    {
      method: 'POST',
      body: {
        name,
      },
    },
  )
}

export const renameFile = ({
  collectionId,
  fileId,
  name,
}) => {
  return api(
    `/library/collections/${collectionId}/files/${fileId}`,
    {
      method: 'PATCH',
      body: {
        name,
      },
    },
  )
}

export const deleteFile = ({
  collectionId,
  fileId,
}) => {
  return api(
    `/library/collections/${collectionId}/files/${fileId}`,
    {
      method: 'DELETE',
    },
  )
}

export const moveFile = ({
  collectionId,
  fileId,
  afterFileId,
}) => {
  return api(
    `/library/collections/${collectionId}/files/${fileId}/position`,
    {
      method: 'PATCH',
      body: {
        afterFileId,
      },
    },
  )
}