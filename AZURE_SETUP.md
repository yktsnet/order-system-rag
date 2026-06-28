# Azure 登録・リソースセットアップ手順

本プロジェクト（RAG パイプライン）で必要となる Azure のリソース（Document Intelligence, AI Search）のセットアップ手順です。

---

## 1. サブスクリプションの確認

すでに Azure にサインインされており、サブスクリプション（例: `Azure subscription 1`）が存在する場合は、**アカウントの新規作成やサブスクリプションの追加は不要**です。その既存のサブスクリプションを使用してリソースを作成します。

---

## 2. リソースグループの作成

**リソースグループ**とは、Azure の各サービス（リソース）をまとめて管理するための「フォルダ」のようなものです。
既存のサブスクリプションの中に、今回のプロジェクト専用のリソースグループを作成することをお勧めします（後から一括削除しやすくなります）。

1. [Azure Portal](https://portal.azure.com/) にサインインします。
2. 上部の検索バーに「**リソース グループ**」（または `Resource groups`）と入力し、検索結果から選択します。
3. 「**作成**」（Create）をクリックします。
4. 以下の項目を設定します：
   - **サブスクリプション**: `Azure subscription 1` (またはお使いの既存のもの)
   - **リソース グループ**: `rg-order-system-rag`（任意の名前）
   - **領域** (Region): `Japan East` (東日本) または `East US` (米国東部) など
5. 「**確認と作成**」 -> 「**作成**」をクリックします。

---

## 3. Azure AI Document Intelligence リソースの作成

PDF から構造化データ（テキスト、テーブル、キーと値のペア）を抽出するために使用します。

1. Azure Portal の検索バーに「**Document Intelligence**」と入力し、検索結果から選択します。
2. 「**作成**」（Create）をクリックします。
3. 以下の項目を設定します：
   - **サブスクリプション**: お使いのサブスクリプション
   - **リソース グループ**: 先ほど作成した `rg-order-system-rag`
   - **地域** (Region): `East US` または `Japan East`
     > [!NOTE]
     > Document Intelligence はリージョンによって利用可能な機能や価格が異なります。通常は `East US` (米国東部) が最も最新の機能が早く提供され、価格も安価な傾向にあります。
   - **名前**: `doc-intel-order-rag`（一意の名前）
   - **価格レベル**: **Free F0**（無料枠。1アカウントあたり1つまで作成可能）
4. 「**確認と作成**」 -> 「**作成**」をクリックします。
5. デプロイ完了後、「**リソースに移動**」をクリックします。
6. 左メニューの「**キーとエンドポイント**」（Keys and Endpoint）をクリックし、以下をメモします：
   - **キー 1** (Key 1)
   - **エンドポイント** (Endpoint)

---

## 4. Azure AI Search リソースの作成

抽出したテキストやベクターデータをインデックス化し、検索可能にするために使用します。

1. Azure Portal の検索バーに「**AI Search**」（旧 Azure Cognitive Search）と入力し、検索結果から選択します。
2. 「**作成**」（Create）をクリックします。
3. 以下の項目を設定します：
   - **サブスクリプション**: お使いのサブスクリプション
   - **リソース グループ**: `rg-order-system-rag`
   - **サービス名**: `search-order-rag`（全世界で一意の小文字・数字のみの名前）
   - **場所** (Location): `East US` などの Document Intelligence と同じリージョンを推奨
   - **価格レベル**: 「価格レベルの変更」をクリックし、**Free**（無料枠。1サブスクリプションあたり1つまで）を選択します。
4. 「**確認と作成**」 -> 「**作成**」をクリックします。
5. デプロイ完了後、「**リソースに移動**」をクリックします。
6. 左メニューの「**キー**」（Keys）をクリックし、以下をメモします：
   - **プライマリ管理者キー** (Primary admin key)
7. 概要ページに表示されている「**URL**」（例: `https://search-order-rag.search.windows.net`）をコピーしてメモします。

---

## 5. 環境変数の設定

取得したキーとエンドポイントをプロジェクトに設定します。

1. プロジェクトのルートディレクトリにある `.env.example` コピーして `.env` ファイルを作成します。
   ```bash
   cp .env.example .env
   ```
2. `.env` ファイルを開き、メモした値を入力します。

```env
# Azure Document Intelligence 設定
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=<メモした Document Intelligence のエンドポイント>
AZURE_DOCUMENT_INTELLIGENCE_KEY=<メモした Document Intelligence のキー 1>

# Azure AI Search 設定
AZURE_SEARCH_SERVICE_ENDPOINT=<メモした AI Search の URL>
AZURE_SEARCH_ADMIN_KEY=<メモした AI Search のプライマリ管理者キー>
AZURE_SEARCH_INDEX_NAME=order-system-rag-index

# Gemini API 設定 (生成AIのデフォルトモデルとして使用)
GEMINI_API_KEY=<お持ちの Gemini API キー>
```

---

## 次のステップ

環境変数の設定が完了したら、`TASK.md` の **1-1. Azure リソース準備** のチェックボックスを埋め、**1-2. 取り込み（Document Intelligence）** の実装に進むことができます。
