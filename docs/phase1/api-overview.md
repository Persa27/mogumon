# API基本設計（フェーズ1）

## 1. エンドポイント一覧（MVP）
- `POST /api/sessions` セッション開始
- `POST /api/sessions/{id}/taps` タップ記録
- `POST /api/sessions/{id}/finish` セッション終了
- `GET /api/sessions/{id}/result` 結果取得
- `GET /api/children/{childId}/history` 履歴取得
- `GET /api/children/{childId}/monster` モンスター状態取得

## 2. タップ記録APIの責務
- タップ受信時刻を記録
- 前回有効タップとの差分で有効/無効判定
- コンボ継続判定
- エサ種別に応じた属性ポイント加算
- レスポンスで現在のコンボと反映後ポイントを返却

## 3. エラー方針（基本）
- 400: 入力不正
- 401: 未認証
- 403: 権限不足
- 404: セッション未検出
- 409: セッション状態不整合（終了済み等）
- 500: サーバー内部エラー
