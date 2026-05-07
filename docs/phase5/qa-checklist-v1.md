# QAチェックリスト v1

## 機能
- [ ] bootstrapでdevice_token発行
- [ ] session作成・終了が可能
- [ ] tapでポイント増加
- [ ] 連打tapが無効化される
- [ ] result/history/health取得

## 信頼性
- [ ] サーバー再起動後に状態復元
- [ ] state.json破損時に起動継続

## セキュリティ
- [ ] 無効tokenで404
- [ ] JSON不正で400

## リリース前
- [ ] テスト一式パス
- [ ] 主要手動シナリオ確認
