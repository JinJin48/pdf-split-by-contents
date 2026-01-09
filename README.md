# pdf-split-by-contents

大容量PDFファイルをブックマーク構造またはページ範囲で分割するツール。

## 機能

- **自動分割**: PDFのブックマーク（目次）構造に基づいて節（Level 3）単位で分割
- **手動分割**: ページ範囲を指定して任意の位置で分割
- **メタデータ付与**: 分割時に書籍情報・章情報をYAMLファイルとして出力

## インストール

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本的な使い方

```bash
# input_pdf/ フォルダ内の全PDFを処理
python pdf-split-by-contents.py

# 単一のPDFファイルを処理
python pdf-split-by-contents.py document.pdf

# 出力先を指定
python pdf-split-by-contents.py -o custom_output

# ブックマークがない場合はスキップ
python pdf-split-by-contents.py --no-split

# バックグラウンドモード（ブックマークなしはスキップ）
python pdf-split-by-contents.py --background

# メタデータ付きで分割
python pdf-split-by-contents.py document.pdf \
  --title "薬機法の実務解説" \
  --author "山田太郎" \
  --isbn "9784123456789" \
  --publisher "法律出版社" \
  --published-date "2024-04-01" \
  --genre "法律/医薬品" \
  --description "薬機法の実務について解説した書籍"
```

### オプション

| オプション | 説明 |
|------------|------|
| `pdf` | 処理するPDFファイルのパス（省略時は`input_pdf/`内の全PDF） |
| `-o, --output` | 出力ディレクトリ（デフォルト: `split_pdf`） |
| `--no-split` | ブックマークがない場合、分割せずスキップ |
| `--background` | GUIプロンプトなしで実行（ブックマークなしはスキップ） |
| `--title` | 元の本のタイトル |
| `--isbn` | ISBN（13桁） |
| `--author` | 著者名 |
| `--publisher` | 出版社 |
| `--published-date` | 発行日（YYYY-MM-DD形式） |
| `--genre` | ジャンル |
| `--description` | 本の概要 |

## フォルダ構成

```
pdf-split-by-contents/
├── pdf-split-by-contents.py  # メインスクリプト
├── common.py                 # 共通ユーティリティ
├── requirements.txt          # 依存パッケージ
├── input_pdf/                # 入力PDF配置
└── split_pdf/                # 分割されたPDFの出力先
```

## 分割ロジック

1. ブックマーク（目次）がある場合:
   - 節（Level 3）単位で分割
   - 節がない章はそのまま章（Level 2）単位で分割

2. ブックマークがない場合:
   - 通常モード: ユーザーにページ範囲を入力してもらう（キャンセルでスキップ）
   - `--no-split`指定時: 分割せずスキップ
   - `--background`指定時: 分割せずスキップ（警告メッセージ出力）

## 出力ファイル

### PDFファイル

```
000_00_Contents.pdf
001_Chapter1_Introduction.pdf
002_Chapter2_Getting_Started.pdf
...
```

### メタデータファイル（YAML）

各PDFファイルに対応する`.yaml`ファイルが生成されます。

```yaml
---
parent_document: 薬機法解説書.pdf
parent_title: 薬機法の実務解説
isbn: 9784123456789
author: 山田太郎
publisher: 法律出版社
published_date: 2024-04-01
genre: 法律/医薬品
description: 薬機法の実務について解説した書籍
chapter_number: 3
chapter_title: 第3章 製造販売承認
total_chapters: 12
split_index: 3
split_date: 2025-01-09
---
```

**注意**: 指定されていないオプションはYAMLファイルに出力されません。

## ライセンス

MIT License
