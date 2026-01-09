# CLAUDE.md

このファイルはClaude Codeがこのリポジトリで作業する際のガイドです。

## プロジェクト概要

大容量PDFファイルをブックマーク構造またはページ範囲で分割するツール。

### 主な機能

- **自動分割**: PDFのブックマーク（目次）構造に基づいて節（Level 3）単位で分割
- **手動分割**: ページ範囲を指定して任意の位置で分割
- **ISBN自動抽出**: ファイル名からISBNを自動抽出（ハイフン自動除去）
- **メタデータ自動取得**: Google Books APIから書籍情報を自動取得
- **スキップ機能**: ブックマークがないPDFを分割せずスキップ（--no-split）
- **バックグラウンドモード**: GUIなしで自動処理（ブックマークなしはスキップ）
- **メタデータ付与**: 分割時に書籍情報・章情報をYAMLファイルとして出力

### 用途

- 大きなPDFを章・節単位で分割
- pdf-converter-4-difyの前処理として使用（分割後にMarkdown変換）

## ディレクトリ構造

```
pdf-split-by-contents/
├── pdf-split-by-contents.py  # メインスクリプト
├── common.py                 # 共通ユーティリティ（設定、ロギング、ISBN抽出、API連携）
├── requirements.txt          # 依存パッケージ
├── input_pdf/                # 入力PDFを配置
│   └── .gitkeep
├── split_pdf/                # 分割されたPDFの出力先
│   └── .gitkeep
├── .gitignore
├── CLAUDE.md                 # 本ファイル
└── README.md
```

## 技術スタック

| 技術 | バージョン | 用途 |
|------|-----------|------|
| Python | 3.10+ | メイン言語 |
| PyMuPDF (fitz) | 1.23.0+ | PDF解析・分割 |
| tkinter | 標準 | GUIダイアログ |
| urllib | 標準 | Google Books API連携 |

### 主要モジュール

**pdf-split-by-contents.py**
- `PdfSplitter`: PDF分割クラス
  - `split_smart()`: ブックマーク構造に基づく自動分割
  - `split_manually()`: ページ範囲指定による手動分割
  - `_save_ranges()`: ページ範囲をPDFファイルとして保存、YAMLメタデータ生成
  - `_write_metadata_yaml()`: YAMLメタデータファイル生成
- `split_pdf()`: 単一PDF処理のエントリーポイント
- `main()`: CLI引数処理、ISBN抽出、API取得、メタデータ上書き

**common.py**
- `INPUT_DIR`, `OUTPUT_DIR`: 入出力ディレクトリ設定
- `LOG_FILE`: ログファイルパス（pdf-split.log）
- `LARGE_FILE_THRESHOLD`: 分割対象サイズ閾値（45MB）
- `GOOGLE_BOOKS_API_URL`: Google Books API URL
- `setup_logging()`: ロギング設定
- `estimate_time()`: 残り時間推定
- `clean_filename()`: ファイル名サニタイズ
- `extract_isbn_from_filename()`: ファイル名からISBN抽出
- `fetch_metadata_from_google_books()`: Google Books APIからメタデータ取得

## 現在の開発状況

### 完了済み

- ブックマーク構造（Level 2/3）に基づく自動分割
- 手動ページ範囲指定による分割
- --no-split オプション（ブックマークなしはスキップ）
- バックグラウンドモード対応（ブックマークなしはスキップ）
- 進捗推定・ロギング
- ファイル名からISBN自動抽出
- Google Books APIからメタデータ自動取得
- メタデータ上書きオプション

### 既知の課題

- 特になし

## 今後の予定

特に計画された機能追加はありません。

## 開発時の注意事項

### コマンド

```bash
# 依存関係インストール
pip install -r requirements.txt

# input_pdf/内の全PDFを処理（ISBN自動抽出、API取得）
python pdf-split-by-contents.py

# 単一PDF処理（ファイル名からISBN抽出）
python pdf-split-by-contents.py 978-1234567890_BookTitle.pdf

# 出力先指定
python pdf-split-by-contents.py -o custom_output

# ブックマークがない場合はスキップ
python pdf-split-by-contents.py --no-split

# バックグラウンドモード（ブックマークなしはスキップ）
python pdf-split-by-contents.py --background

# ジャンルを手動指定（API取得が粗いため推奨）
python pdf-split-by-contents.py 978-xxx.pdf --genre "法律/医薬品"

# メタデータを上書き
python pdf-split-by-contents.py 978-xxx.pdf \
  --title "正確なタイトル" \
  --author "著者名" \
  --genre "法律"
```

### ファイル名形式（ISBN自動抽出）

| 形式 | 例 |
|------|-----|
| `ISBN13_任意.pdf` | `9784123456789_薬機法解説.pdf` |
| `ISBN13.pdf` | `9784123456789.pdf` |
| `ハイフン付き` | `978-4-12-345678-9_Book.pdf` |

- ハイフンは自動除去
- 13桁でない場合：エラー出力
- 数字以外が含まれる場合：エラー出力

### メタデータ上書きオプション

| オプション | 説明 |
|------------|------|
| `--title` | 本のタイトル（`parent_document`として出力） |
| `--isbn` | ISBN（ファイル名からの抽出を上書き） |
| `--author` | 著者名 |
| `--publisher` | 出版社 |
| `--published-date` | 発行日（YYYY-MM-DD形式） |
| `--genre` | ジャンル（API取得が粗いため手動推奨） |
| `--description` | 本の概要 |
| `--language` | 言語コード（例: ja, en） |

### 分割ロジック

1. ファイルサイズが45MB未満 → 分割せずそのまま
2. 45MB以上でブックマークあり:
   - Level 2（章）を基準に探索（なければLevel 1にフォールバック）
   - 各章の下にLevel 3（節）があれば節単位で分割
   - 節がなければ章単位で分割
3. 45MB以上でブックマークなし:
   - 通常モード: ユーザーにページ範囲入力を求める（キャンセルでスキップ）
   - --no-split指定時: スキップ
   - --background指定時: スキップ（警告出力）

### 出力ファイル形式

ファイル番号は001から開始します（目次がある場合、目次が001）。

```
001_00_Contents.pdf      # 目次（split_index: 1）
002_Chapter1.pdf         # 第1章（split_index: 2）
003_Chapter2.pdf         # 第2章（split_index: 3）
...
```

### メタデータ取得フロー

1. ファイル名からISBN抽出（`--isbn`指定時は上書き）
2. ISBNがあればGoogle Books APIからメタデータ取得
3. CLI引数で指定された値でAPI取得値を上書き
4. 分割時にYAMLファイルとして出力

### YAML出力例

```yaml
---
parent_document: 薬機法の実務解説
isbn: 9784123456789
author: 山田太郎
publisher: 法律出版社
published_date: 2024-04-01
description: 薬機法について解説
language: ja
genre: 法律/医薬品
chapter_number: 3
chapter_title: 第3章 製造販売承認
total_chapters: 12
split_index: 3
---
```

### ログ

- 処理ログは `pdf-split.log` に出力
