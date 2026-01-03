# CLAUDE.md

このファイルはClaude Codeがこのリポジトリで作業する際のガイドです。

## プロジェクト概要

大容量PDFファイルをブックマーク構造またはページ範囲で分割するツール。

### 主な機能

- **自動分割**: PDFのブックマーク（目次）構造に基づいて節（Level 3）単位で分割
- **手動分割**: ページ範囲を指定して任意の位置で分割
- **固定ページ分割**: 指定ページ数ごとに均等分割
- **バックグラウンドモード**: GUIなしで自動処理

### 用途

- 大きなPDFを章・節単位で分割
- pdf-converter-4-difyの前処理として使用（分割後にMarkdown変換）

## ディレクトリ構造

```
pdf-split/
├── pdf-split.py      # メインスクリプト
├── common.py         # 共通ユーティリティ（設定、ロギング）
├── requirements.txt  # 依存パッケージ
├── input_pdf/        # 入力PDFを配置
│   └── .gitkeep
├── split_pdf/        # 分割されたPDFの出力先（実行時に作成）
├── .gitignore
├── CLAUDE.md         # 本ファイル
└── README.md
```

## 技術スタック

| 技術 | バージョン | 用途 |
|------|-----------|------|
| Python | 3.10+ | メイン言語 |
| PyMuPDF (fitz) | 1.23.0+ | PDF解析・分割 |
| tkinter | 標準 | GUIダイアログ |

### 主要モジュール

**pdf-split.py**
- `PdfSplitter`: PDF分割クラス
  - `split_smart()`: ブックマーク構造に基づく自動分割
  - `split_manually()`: ページ範囲指定による手動分割
  - `split_by_pages()`: 固定ページ数での分割
- `split_pdf()`: 単一PDF処理のエントリーポイント
- `main()`: CLI引数処理

**common.py**
- `INPUT_DIR`, `OUTPUT_DIR`: 入出力ディレクトリ設定
- `LARGE_FILE_THRESHOLD`: 分割対象サイズ閾値（45MB）
- `setup_logging()`: ロギング設定
- `estimate_time()`: 残り時間推定
- `clean_filename()`: ファイル名サニタイズ

## 現在の開発状況

### 完了済み

- ブックマーク構造（Level 2/3）に基づく自動分割
- 手動ページ範囲指定による分割
- 固定ページ数での均等分割
- バックグラウンドモード対応
- 進捗推定・ロギング

### 既知の課題

- ブックマークがないPDFでは手動入力またはデフォルト分割が必要

## 今後の予定

特に計画された機能追加はありません。

## 開発時の注意事項

### コマンド

```bash
# 依存関係インストール
pip install -r requirements.txt

# input_pdf/内の全PDFを処理
python pdf-split.py

# 単一PDF処理
python pdf-split.py document.pdf

# 出力先指定
python pdf-split.py -o custom_output

# バックグラウンドモード
python pdf-split.py --background
```

### 分割ロジック

1. ファイルサイズが45MB未満 → 分割せずそのまま
2. 45MB以上でブックマークあり → 節（Level 3）単位で分割
3. 45MB以上でブックマークなし → 手動入力または50ページ単位

### ログ

- 処理ログは `pdf-split.log` に出力
