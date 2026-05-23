# 注册页面

## 概述

- 路径：`/auth/register`
- 文件：`frontend/src/views/auth/register/RegisterView.vue`（~110 行）
- 功能：用户名 + 邮箱验证码注册

## 组件结构

```
src/
  utils/authRules.ts               ← 共享密码验证规则
  components/
    AuthLayout.vue                 ← 认证页公共布局（背景 + 标题 + 半透明卡片）
    AuthBackground.vue             ← 背景图 + 遮罩层
    AuthHeader.vue                 ← 返回按钮 + 品牌标题
  views/auth/register/RegisterView.vue ← 注册表单
```

## 实现细节

- 表单验证通过 `rules` + `formRef.value?.validate()` 完成，不额外写手动校验
- 密码规则从 `authRules.ts` 共享
- "获取验证码"按钮：调用 `sendVerificationCode(email)`，mock 模式下验证码自动填入输入框
- 发送验证码前用 `validateField('email')` 校验邮箱格式
- 倒计时 60 秒，期间按钮禁用
- 提交注册 → `registerWithEmail({ username, password, email, verification_code })` → 成功后跳转 `/auth/login`
- 错误处理：用户名已存在 → "用户名已存在"；验证码错误 → 提示错误信息；网络失败 → "网络连接失败"

## 验证规则

| 字段 | 规则 |
|------|------|
| 用户名 | 必填，2-50 字符 |
| 邮箱 | 必填，邮箱格式 |
| 验证码 | 必填，6 位数字 |
| 密码 | 必填，最少 6 字符（共享自 `authRules.ts`） |
| 确认密码 | 必填，需与密码一致 |

## 路由守卫

- 已登录用户访问注册页 → 自动跳转首页 `/`
- 注册成功 → 跳转 `/auth/login`
