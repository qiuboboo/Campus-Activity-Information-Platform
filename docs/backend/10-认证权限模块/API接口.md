# 认证接口 API

## `GET /api/auth/captcha`

获取图形验证码。返回 PNG 图片，验证码令牌通过响应头返回。

**权限：** 公开（无需认证）

**速率限制：** 30 次/分钟/IP

**响应头：**
- `X-Captcha-Token`：验证码令牌（UUID 字符串），后续注册/登录时需要提交

**成功响应 (200)：**
```
Content-Type: image/png
X-Captcha-Token: 7417777e-7189-4405-90c4-09883b3e2b3f
```
（返回 PNG 二进制图片数据）

**使用流程：**
1. 前端先请求此接口获取验证码图片并展示给用户
2. 用户输入验证码中的数字
3. 注册/登录时提交 `captcha_token`（从响应头获取）和 `captcha_code`（用户输入值）

---

## `POST /api/auth/send-code`

发送邮箱验证码。接收邮箱地址，生成 6 位数字验证码存入 Redis（5 分钟有效，60 秒冷却），通过 SMTP 发送邮件。

**权限：** 公开（无需认证）

**速率限制：** 5 次/分钟/IP

**请求体：**
```json
{
  "email": "user@example.com"
}
```

**字段说明：**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `email` | string | 是 | 接收验证码的邮箱地址，需符合 email 格式 |

**成功响应 (200)：**
```json
{
  "message": "验证码已发送",
  "expires_in": 300
}
```

**错误码：**
- `400`：邮箱格式不合法（`invalid email address`）
- `429`：60 秒冷却期内，或发送失败（如 SMTP 错误），返回 `{"message": "..."}`
- `500`：服务器内部错误（日志记录详细原因）

---

## `POST /api/auth/register`

注册新用户。默认角色为 `viewer`，可指定 `publisher`。不允许自注册为 `admin`。需携带邮箱验证码和图形验证码。

**权限：** 公开（无需认证）

**速率限制：** 5 次/分钟/IP

**请求体：**
```json
{
  "username": "testuser",
  "password": "test123456",
  "email": "testuser@example.com",
  "role": "viewer",
  "verification_code": "272033",
  "captcha_token": "7417777e-7189-4405-90c4-09883b3e2b3f",
  "captcha_code": "4826"
}
```

**字段说明：**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `username` | string | 是 | 2-50 个字符，全局唯一 |
| `password` | string | 是 | 至少 6 个字符 |
| `email` | string | 是 | 合法邮箱格式，全局唯一 |
| `role` | string | 否 | `viewer`（默认）或 `publisher`，不允许 `admin` |
| `verification_code` | string | 是（非测试环境） | 6 位数字邮箱验证码 |
| `captcha_token` | string | 是 | 图形验证码令牌 |
| `captcha_code` | string | 是 | 图形验证码用户输入值 |

**成功响应 (201)：**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 2,
    "username": "testuser",
    "email": "testuser@example.com",
    "role": "viewer",
    "created_at": "2026-05-21T09:45:41"
  }
}
```

**错误码：**
- `400`（参数校验失败）：
  - `username and password are required`：缺少用户名或密码
  - `invalid or missing captcha`：图形验证码错误或已过期
  - `username must be 2-50 characters`：用户名长度不合法
  - `password must be at least 6 characters`：密码太短
  - `role must be 'viewer' or 'publisher'`：角色不合法
  - `valid email is required`：缺少或邮箱格式不合法
  - `invalid or missing verification code`：邮箱验证码错误或已过期
- `409`（冲突）：
  - `username already exists`：用户名已被注册
  - `email already registered`：邮箱已被注册

---

## `POST /api/auth/login`

用户登录并获取 JWT。支持用户名或邮箱登录。需携带图形验证码。

**权限：** 公开（无需认证）

**速率限制：** 10 次/分钟/IP

**请求体（使用用户名）：**
```json
{
  "username": "admin",
  "password": "admin123456",
  "captcha_token": "7417777e-7189-4405-90c4-09883b3e2b3f",
  "captcha_code": "4826"
}
```

**请求体（使用邮箱）：**
```json
{
  "email": "admin@example.com",
  "password": "admin123456",
  "captcha_token": "7417777e-7189-4405-90c4-09883b3e2b3f",
  "captcha_code": "4826"
}
```

**字段说明：**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `username` | string | 二选一 | 用户名，与 email 二选一 |
| `email` | string | 二选一 | 邮箱地址，与 username 二选一 |
| `password` | string | 是 | 用户密码 |
| `captcha_token` | string | 是 | 图形验证码令牌 |
| `captcha_code` | string | 是 | 图形验证码用户输入值 |

**成功响应 (200)：**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "created_at": "2026-01-01T00:00:00"
  }
}
```

**JWT 附加声明：**
- `role`：用户角色
- `username`：用户名

**错误码：**
- `400`：
  - `username/email and password are required`：缺少用户名/邮箱或密码
  - `invalid or missing captcha`：图形验证码错误或已过期
- `401`：`invalid credentials`——用户名/邮箱或密码错误

---

## `GET /api/auth/me`

获取当前登录用户信息。

**权限：** 需 JWT 认证（`@jwt_required()`）

**请求头：**
```
Authorization: Bearer <jwt-token>
```

**成功响应 (200)：**
```json
{
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "created_at": "2026-01-01T00:00:00"
  }
}
```

**错误码：**
- `401`：未提供或无效的 JWT
- `404`：用户不存在（JWT 中的用户 ID 在数据库中已删除）
