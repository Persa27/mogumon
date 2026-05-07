# テスト設計 v1

## 対象
- `src/app.py` HTTP API

## 観点
- 正常系: bootstrap, session, tap, finish, result, history, health
- 異常系: 連打tap無効化、不正トークン、JSON不正
- 境界値: history `limit` の下限/上限

## 実施レベル
- 結合テスト（in-process HTTPServer）

## 追加予定
- 永続化ファイル破損時の復旧確認
- 429相当（将来のレート制御）
- E2E（ブラウザ自動操作）
