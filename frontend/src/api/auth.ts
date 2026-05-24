import client from './client'

export interface CaptchaData {
  imageUrl: string
  captchaToken: string
}

/** Fetch captcha image and extract the token from X-Captcha-Token header. */
export async function getCaptcha(): Promise<CaptchaData> {
  const resp = await fetch('/api/auth/captcha')
  if (!resp.ok) throw new Error('Failed to fetch captcha')
  const blob = await resp.blob()
  const imageUrl = URL.createObjectURL(blob)
  const captchaToken = resp.headers.get('X-Captcha-Token') || ''
  return { imageUrl, captchaToken }
}

export interface LoginRequest {
  username: string
  password: string
  captcha_token?: string
  captcha_code?: string
}

export interface LoginResponse {
  token?: string
  message?: string
  user: {
    id: number
    username: string
    role: string
    email?: string
    created_at: string
  } | null
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
  email?: string
  verification_code?: string
  captcha_token?: string
  captcha_code?: string
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
  captcha_token?: string
  captcha_code?: string
}

export function registerWithEmail(data: RegisterVerifyRequest) {
  return client.post('/auth/register', data)
}
