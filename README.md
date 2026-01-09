# pdf-split-by-contents

大容量PDFファイルをブックマーク構造またはページ範囲で分割するツール。

## 機能

- **自動分割**: PDFのブックマーク（目次）構造に基づいて節（Level 3）単位で分割
- **手動分割**: ページ範囲を指定して任意の位置で分割
- **ISBN自動抽出**: ファイル名からISBNを自動抽出
- **メタデータ自動取得**: Google Books APIから書籍情報を自動取得
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

# 単一のPDFファイルを処理（ISBN自動抽出）
python pdf-split-by-contents.py 978-1234567890_BookTitle.pdf

# 出力先を指定
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

以下の形式でファイル名にISBNを含めると、自動抽出されます：

| 形式 | 例 |
|------|-----|
| `ISBN13_任意.pdf` | `9784123456789_薬機法解説.pdf` |
| `ISBN13.pdf` | `9784123456789.pdf` |
| `ハイフン付き` | `978-4-12-345678-9_Book.pdf` |

- ハイフンは自動除去されます
- 13桁でない場合はエラー出力
- 数字以外が含まれる場合はエラー出力

### オプション

| オプション | 説明 |
|------------|------|
| `pdf` | 処理するPDFファイルのパス（省略時は`input_pdf/`内の全PDF） |
| `-o, --output` | 出力ディレクトリ（デフォルト: `split_pdf`） |
| `--no-split` | ブックマークがない場合、分割せずスキップ |
| `--background` | GUIプロンプトなしで実行（ブックマークなしはスキップ） |

### メタデータ上書きオプション

Google Books APIから自動取得した値を上書きできます：

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

**注意**:
- ISBNがファイル名から抽出できない場合、API取得はスキップされます
- API取得に失敗した場合、エラーを出力して処理を継続します
- 指定されていないオプションはYAMLファイルに出力されません

## ライセンス

MIT License
