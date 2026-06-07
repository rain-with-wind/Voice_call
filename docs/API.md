# API 文档

本文档描述 `public_backend` 提供的核心 HTTP 接口。

## 基础信息

- 基础路径：`/api`
- 数据格式：`application/json`
- 房间管理鉴权：通过请求头 `X-Manage-Token`

## 1. 健康检查

### `GET /api/health`

用于确认后端服务是否在线。

示例响应：

```json
{
  "ok": true,
  "service": "public-voice-call-backend"
}
```

## 2. 创建房间

### `POST /api/rooms/register`

请求体：

```json
{
  "name": "Team Room",
  "public_host": "voice.example.com",
  "public_port": 5000,
  "owner_name": "",
  "notes": ""
}
```

成功响应：

```json
{
  "room": {
    "room_code": "ABC123",
    "name": "Team Room",
    "public_host": "voice.example.com",
    "public_port": 5000,
    "owner_name": "",
    "notes": "",
    "status": "active",
    "created_at": "2026-06-07T08:00:00+00:00",
    "updated_at": "2026-06-07T08:00:00+00:00",
    "last_heartbeat_at": "2026-06-07T08:00:00+00:00"
  },
  "manage_token": "server-issued-token",
  "heartbeat_interval_seconds": 15
}
```

说明：

- `manage_token` 仅在创建时返回，用于后续维护和关闭房间
- 前端虽然对用户隐藏了“心跳”术语，但该字段在 API 层仍保留，作为内部实现细节

## 3. 查询在线房间列表

### `GET /api/rooms`

成功响应：

```json
{
  "rooms": [
    {
      "room_code": "ABC123",
      "name": "Team Room",
      "public_host": "voice.example.com",
      "public_port": 5000,
      "owner_name": "",
      "notes": "",
      "status": "active",
      "created_at": "2026-06-07T08:00:00+00:00",
      "updated_at": "2026-06-07T08:00:00+00:00",
      "last_heartbeat_at": "2026-06-07T08:00:00+00:00"
    }
  ]
}
```

## 4. 查询单个房间

### `GET /api/rooms/{room_code}`

成功响应：

```json
{
  "room": {
    "room_code": "ABC123",
    "name": "Team Room",
    "public_host": "voice.example.com",
    "public_port": 5000,
    "owner_name": "",
    "notes": "",
    "status": "active",
    "created_at": "2026-06-07T08:00:00+00:00",
    "updated_at": "2026-06-07T08:00:00+00:00",
    "last_heartbeat_at": "2026-06-07T08:00:00+00:00"
  }
}
```

失败时返回：

```json
{
  "error": "Room not found or expired"
}
```

## 5. 更新房间在线状态

### `POST /api/rooms/{room_code}/heartbeat`

请求头：

```text
X-Manage-Token: server-issued-token
```

请求体：

```json
{}
```

成功响应为最新房间信息。

## 6. 关闭房间

### `POST /api/rooms/{room_code}/close`

请求头：

```text
X-Manage-Token: server-issued-token
```

请求体：

```json
{}
```

成功响应：

```json
{
  "message": "Room closed"
}
```

## 错误处理

常见错误码：

- `400`：请求参数非法
- `401`：缺少管理令牌
- `404`：房间不存在、已过期，或管理令牌无效

CLI 中的 `PublicBackendClient` 会把后端错误统一包装为 `RuntimeError`，便于命令行直接输出友好提示。
