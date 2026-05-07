# API詳細設計 v1

## エラーレスポンス

全APIで以下形式を採用:

```json
{"error":{"code":"<snake_case>","message":"<human readable>"}}
```

主な code:
- `invalid_json`
- `device_session_not_found`
- `session_not_found`
- `session_finished`
- `invalid_session_id`
- `not_found`

## 主要エンドポイント

- `POST /api/device-session/bootstrap`
- `POST /api/sessions`
- `POST /api/sessions/{id}/taps`
- `POST /api/sessions/{id}/finish`
- `GET /api/sessions/{id}/result`
- `GET /api/sessions/history?limit=20`
- `GET /api/device-session/monster`
- `GET /api/health`

## 履歴API

`limit` クエリを導入（1〜100に丸める）。

## 永続化

- 保存先: `data/state.json`
- 保存タイミング: bootstrap/session作成/tap/finish/monster状態遷移後
- 起動時に `load_state()` で復元
