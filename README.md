# PDF Splitter

大容量PDFファイルをブックマーク構造またはページ範囲で分割するツール。

## 機能

- **自動分割**: PDFのブックマーク（目次）構造に基づいて節（Level 3）単位で分割
- **手動分割**: ページ範囲を指定して任意の位置で分割

## インストール

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本的な使い方

```bash
# input_pdf/ フォルダ内の全PDFを処理
python pdf-split.py

# 単一のPDFファイルを処理
python pdf-split.py document.pdf

# 出力先を指定
python pdf-split.py -o custom_output

# ブックマークがない場合はスキップ
python pdf-split.py --no-split

# バックグラウンドモード（ブックマークなしはスキップ）
python pdf-split.py --background
```

### オプション

| オプション | 説明 |
|------------|------|
| `pdf` | 処理するPDFファイルのパス（省略時は`input_pdf/`内の全PDF） |
| `-o, --output` | 出力ディレクトリ（デフォルト: `split_pdf`） |
| `--no-split` | ブックマークがない場合、分割せずスキップ |
| `--background` | GUIプロンプトなしで実行（ブックマークなしはスキップ） |

## フォルダ構成

```
pdf-split/
├── pdf-split.py      # メインスクリプト
├── common.py         # 共通ユーティリティ
├── requirements.txt  # 依存パッケージ
├── input_pdf/        # 入力PDFを配置
└── split_pdf/        # 分割されたPDFの出力先
```

## 分割ロジック

1. ブックマーク（目次）がある場合:
   - 節（Level 3）単位で分割
   - 節がない章はそのまま章（Level 2）単位で分割

2. ブックマークがない場合:
   - 通常モード: ユーザーにページ範囲を入力してもらう（キャンセルでスキップ）
   - `--no-split`指定時: 分割せずスキップ
   - `--background`指定時: 分割せずスキップ（警告メッセージ出力）

## 出力ファイル名

```
000_00_Contents.pdf
001_Chapter1_Introduction.pdf
002_Chapter2_Getting_Started.pdf
...
```

## ライセンス

MIT License
