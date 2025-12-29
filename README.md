# PDF Splitter

大容量PDFファイルをブックマーク構造またはページ範囲で分割するツール。

## 機能

- **自動分割**: PDFのブックマーク（目次）構造に基づいて自動的にチャプター単位で分割
- **手動分割**: ページ範囲を指定して任意の位置で分割
- **強制分割**: 50ページ超のセクションは自動的にさらに分割
- **進捗管理**: 処理済みファイルの追跡と再開機能

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

# バックグラウンドモード（GUIプロンプトなし）
python pdf-split.py --background

# 小さいファイルも強制的に分割
python pdf-split.py --force
```

### オプション

| オプション | 説明 |
|------------|------|
| `pdf` | 処理するPDFファイルのパス（省略時は`input_pdf/`内の全PDF） |
| `-o, --output` | 出力ディレクトリ（デフォルト: `split_pdf`） |
| `--force` | 小さいファイルも強制的に分割 |
| `--background` | GUIプロンプトを表示しないバックグラウンドモード |

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
   - レベル2（チャプター）で主分割
   - 50ページ超のチャプターはレベル3（セクション）でさらに分割
   - セクションがない場合は50ページ単位で強制分割

2. ブックマークがない場合:
   - 対話モード: ユーザーにページ範囲を入力してもらう
   - バックグラウンドモード: 50ページ単位で自動分割

## 出力ファイル名

```
000_Frontmatter.pdf
001_Chapter1_Introduction.pdf
002_Chapter2_Getting_Started.pdf
...
```

## ライセンス

MIT License
