# 登录页面

## 概述

- 路径：`/auth/login`
- 文件：`frontend/src/views/auth/login/LoginView.vue`（~85 行）
- 功能：用户名/邮箱 + 密码登录，支持记住用户名

## 组件结构

```
src/
  utils/authRules.ts               ← 共享密码验证规则
  components/
    AuthLayout.vue                 ← 认证页公共布局（背景 + 标题 + 半透明卡片）
    AuthBackground.vue             ← 背景图 + 遮罩层
    AuthHeader.vue                 ← 返回按钮 + 品牌标题
  views/auth/login/LoginView.vue   ← 登录表单
```

## 实现细节

- 表单验证通过 `rules` + `formRef.value?.validate()` 完成，不额外写手动校验
- 密码规则从 `authRules.ts` 共享
- 提交成功 → `router.replace('/')`，不保留登录页历史
- 记住用户名 → `localStorage.setItem('remembered_user')`
- 错误处理：invalid credentials → "用户名或密码错误"；网络失败 → "网络连接失败"
- "忘记密码"链接 → 跳转 `/auth/forgot-password`（当前 404，待实现）
- "去注册"链接 → `/auth/register`

## 验证规则

| 字段 | 规则 |
|------|------|
| 用户名/邮箱 | 必填，2-50 字符 |
| 密码 | 必填，最少 6 字符（共享自 `authRules.ts`） |

## 路由守卫

- 已登录用户访问登录页 → 自动跳转首页 `/`
- 登录成功 → `router.replace('/')`
- 支持 `?redirect=` 参数（由路由守卫注入），当前版本登录后未使用该参数
