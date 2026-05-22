import client from './client'

export function internalSearch(q: string) {
  return client.get('/search/internal', { params: { q } })
}

export function externalSearch(q: string) {
  return client.get('/search/external', { params: { q } })
}
