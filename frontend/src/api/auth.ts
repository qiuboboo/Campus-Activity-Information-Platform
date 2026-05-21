import client from './client'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  token: string
  user: {
    id: number
    username: string
    role: string
    created_at: string
  }
}

export function login(data: LoginRequest) {
  return client.post<LoginResponse>('/auth/login', data)
}

export function getMe() {
  return client.get('/auth/me')
}
