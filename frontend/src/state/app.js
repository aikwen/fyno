import { reactive } from 'vue'
import {
  GetStartupState,
  OpenService,
} from '../../wailsjs/go/app/App.js'

export const appState = reactive({
  view: 'loading',
  rootDir: '',
  error: '',
})

let opening = false

function applyWorkspaceResult(result) {
  appState.rootDir = result?.rootDir ?? ''
  appState.error = result?.error ?? ''
  appState.view = result?.ready === true ? 'workspace' : 'welcome'
}

export async function initialize() {
  appState.view = 'loading'
  appState.error = ''

  try {
    applyWorkspaceResult(await GetStartupState())
  } catch (error) {
    console.error('初始化 Fyno 失败:', error)
    appState.view = 'welcome'
    appState.error = '初始化应用失败，请稍后重试'
  }
}

export async function openService(rootDir) {
  if (opening) {
    return false
  }

  opening = true
  appState.error = ''
  try {
    const result = await OpenService(rootDir)
    applyWorkspaceResult(result)
    return result?.ready === true
  } catch (error) {
    console.error('打开工作目录失败:', error)
    appState.rootDir = rootDir
    appState.view = 'welcome'
    appState.error = '打开工作目录失败，请稍后重试'
    return false
  } finally {
    opening = false
  }
}
