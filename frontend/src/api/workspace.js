import { api } from './client'

export const getWorkspace = () => {
  return api('/library/workspace')
}

export const updateWorkspace = ({
  directory,
}) => {
  return api('/library/workspace', {
    method: 'PATCH',
    body: {
      directory,
    },
  })
}

export const searchDirectories = ({
  path,
  limit = 20,
}) => {
  return api('/filesystem/directories', {
    query: {
      path,
      limit,
    },
  })
}

export const reloadWorkspace = () => {
  return api('/library/workspace/reload', {
    method: 'POST',
  })
}

export const rebuildWorkspace = () => {
  return api('/library/workspace/rebuild', {
    method: 'POST',
  })
}