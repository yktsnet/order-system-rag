# conventions

## パッケージ構成

- モジュールごとに `src/{module}/` ディレクトリ + `__init__.py`
- エントリポイントスクリプトは `src/` 直下に置く（例: `generate_samples.py`）
- 各スクリプトファイルの先頭 docstring に実行コマンドを記載する（self-documenting）

## 命名規則

- ファイル・モジュール・関数・変数: snake_case
- クラス: PascalCase（Pydantic モデルは `Request` / `Model` サフィックス）
- 定数: UPPER_SNAKE_CASE（`RELEVANCE_THRESHOLD`, `EMBEDDING_MODEL` 等）

## 型ヒント

Python 3.10+ 記法を使う: `list[float]`、`float | None`（`Optional[float]` は使わない）

## データ構造

- ビジネスロジックを持たない純データは `@dataclass` を使う（`SearchResult`、`RagResponse`）
- API の入出力は `pydantic.BaseModel` を使う

## 環境変数

- `python-dotenv` で `PROJECT_ROOT / ".env"` を読み込む（各スクリプトの先頭で `load_dotenv` 呼び出し）
- 必須キー: `os.environ["KEY"]`（値がなければ KeyError で即落ち）
- 省略可能キー: `os.environ.get("KEY", default)`

## エラーハンドリング

- バッチスクリプト（`extract.py`）: ファイルごとに try/except し、エラー件数をカウントして続行
- FastAPI エンドポイント: 例外処理は framework のデフォルトに委ねる（追加ハンドラを書かない）

## 外部クライアント

- `AzureKeyCredential` で認証
- クライアントは毎リクエスト初期化する（シングルトンなし）
- embedding / 生成モデル名は UPPER_SNAKE_CASE 定数で管理する
