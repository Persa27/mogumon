# MVPモンスター画像生成（SVG）

MVP仕様変更により、モンスター画像は PNG ではなく **SVG** を利用します。

4体 × (待機/食事/進化) のSVGを一括生成するスクリプト:

- `scripts/generate_monster_svg_assets.py`

## 実行方法

```bash
python scripts/generate_monster_svg_assets.py
```

## 出力先

- `static/monsters/<monster>/idle/frame1.svg`
- `static/monsters/<monster>/eat/frame1.svg`
- `static/monsters/<monster>/evolve/frame1.svg`
- `static/monsters/<monster>/portrait.svg`

モンスター名:
- `momo`
- `pafu`
- `gabu`
- `fuwa`

## 補足

- 本スクリプトはOpenAI APIキー不要です。
- MVPでは軽量・差し替え容易性を優先し、SVGを採用します。
