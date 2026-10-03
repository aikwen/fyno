import { ofetch } from 'ofetch'

import { config } from '@/config'

export const api = ofetch.create({
  baseURL: config.apiBaseUrl,

  /*
   * ofetch 对普通对象 body
   * 会自动 JSON.stringify，
   * 同时自动设置 JSON Content-Type。
   *
   * 所以这里不需要手动设置：
   * Content-Type: application/json
   */
  onRequest({ request, options }) {
    /*
     * 后续如果需要全局认证，
     * 可以统一在这里处理。
     *
     * 例如：
     *
     * const token = ...
     *
     * if (token) {
     *   options.headers.set(
     *     'Authorization',
     *     `Bearer ${token}`,
     *   )
     * }
     */

    if (import.meta.env.DEV) {
      console.debug(
        '[API Request]',
        options.method ?? 'GET',
        request,
      )
    }
  },

  onResponse({
    request,
    response,
  }) {
    if (import.meta.env.DEV) {
      console.debug(
        '[API Response]',
        response.status,
        request,
      )
    }
  },

  onResponseError({
    request,
    response,
  }) {
    console.error(
      '[API Error]',
      response.status,
      request,
      response._data,
    )
  },
})