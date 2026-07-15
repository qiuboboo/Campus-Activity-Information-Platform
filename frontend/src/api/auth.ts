import client from './client'
import type { UserRole } from './types'

export interface LoginRequest {
  username: string
  password: string
  captcha_token: string
  captcha_code: string
}

export interface LoginResponse {
  token?: string
  message?: string
  user: {
    id: number
    username: string
    role: UserRole
    created_at: string
  } | null
}

export function login(data: LoginRequest) {
  return client.post<LoginResponse>('/auth/login', data)
}

export function getMe(timeout = 8000) {
  return client.get<{ user: LoginResponse['user'] } | LoginResponse['user']>('/auth/me', { timeout })
}

export interface CaptchaChallenge {
  token: string
  imageUrl: string
}

export async function getCaptcha(): Promise<CaptchaChallenge> {
  const response = await client.get<Blob>('/auth/captcha', { responseType: 'blob' })
  const token = response.headers['x-captcha-token']
  if (!token) throw new Error('验证码令牌缺失')
  return { token, imageUrl: URL.createObjectURL(response.data) }
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
  captcha_token: string
  captcha_code: string
}

export function registerWithEmail(data: RegisterVerifyRequest) {
  return client.post('/auth/register', data)
}

export function requestPasswordReset(email: string) {
  return client.post<{ message: string; implemented?: boolean }>('/auth/forgot-password', { email })
}
