import { defineConfig } from '@playwright/test'

const IS_REAL_BACKEND = process.env.E2E_BACKEND === 'real'

const webServer = IS_REAL_BACKEND
  ? [{ command: 'npm run dev -- --host 127.0.0.1', port: 3000, reuseExistingServer: !process.env.CI, timeout: 20_000 }]
  : [
      { command: 'node mock/index.js', port: 5000, reuseExistingServer: !process.env.CI, timeout: 20_000 },
      { command: 'npm run dev -- --host 127.0.0.1', port: 3000, reuseExistingServer: !process.env.CI, timeout: 20_000 },
    ]

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  use: {
    baseURL: 'http://127.0.0.1:3000',
    trace: 'on-first-retry',
  },
  projects: [{
    name: 'chromium',
    use: {
      browserName: 'chromium',
      launchOptions: {
        // 用本地 Edge 免下载 Chromium (~150MB, 国内网络常超时)
        executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
      },
    },
  }],
  webServer,
})
