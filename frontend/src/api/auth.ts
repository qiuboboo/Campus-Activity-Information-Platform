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

export interface RegisterRequest {
  username: string
  password: string
  role?: string
}

export function register(data: RegisterRequest) {
  return client.post('/auth/register', data)
}

export function sendVerificationCode(email: string) {
  return client.post<{ message: string; code?: string }>('/auth/send-code', { email })
}

export interface RegisterVerifyRequest {
  username: string
  password: string
  email: string
  verification_code: string
}

export function registerWithEmail(data: RegisterVerifyRequest) {
  return client.post('/auth/register', data)
}
