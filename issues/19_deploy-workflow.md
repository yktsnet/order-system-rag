## デプロイの CI 自動化
id: 19
branch-slug: deploy-workflow
github_issue:
status: open
type: feat
対象: .github/workflows/deploy.yml (新規)
内容: 現状 `infrastructure/deploy.sh` は手動実行前提で、main への push が本番（SV6）に自動反映されない。attendance-system-migration / order-system-migration と同じ Tailscale + SSH + `docker compose up -d --build` パターンで push 時に自動デプロイされるようにする。
確認: GitHub Actions 上で deploy ジョブが成功し、SSH 先で `docker compose ps` のコンテナが再作成されていることを確認する

---

### 背景

`order-system-rag` は `infrastructure/deploy.sh`（rsync + SSH + `docker compose up -d --build`）を持つが、これを呼び出す GitHub Actions ワークフローが存在しない。そのため main への push 後、フロントエンド／バックエンドの変更が SV6 上のコンテナに反映されず、都度手動で `deploy.sh` を実行する必要があった（実際にフロント修正が反映されず気づいた経緯あり）。

他の常時稼働リポ（attendance-system-migration, order-system-migration, taikan-base-weather, training-scheduler）はすべて `.github/workflows/deploy.yml` を持ち、push だけで自動デプロイされる。本リポだけこのパターンから外れているため揃える。

### 実装方針

`attendance-system-migration/.github/workflows/deploy.yml` を土台に、本リポ用に適用する。テスト用DBサービスなど本リポに不要な部分は削る。

```yaml
name: Deploy
on:
  push:
    branches: [main]

env:
  APP_PATH: /home/${{ secrets.DEPLOY_USER }}/github-public/order-system-rag

jobs:
  deploy:
    name: Deploy
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Connect to Tailscale
        uses: tailscale/github-action@v3
        with:
          oauth-client-id: ${{ secrets.TS_OAUTH_CLIENT_ID }}
          oauth-secret: ${{ secrets.TS_OAUTH_SECRET }}
          tags: tag:ci

      - name: Setup SSH key
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_ed25519
          chmod 600 ~/.ssh/id_ed25519
          ssh-keyscan -H ${{ secrets.DEPLOY_HOST }} >> ~/.ssh/known_hosts

      - name: Sync files to server
        run: |
          rsync -az --delete \
            --exclude='.git' \
            --exclude='node_modules' \
            --exclude='src/web/node_modules' \
            --exclude='.env' \
            -e "ssh -i ~/.ssh/id_ed25519" \
            . ${{ secrets.DEPLOY_USER }}@${{ secrets.DEPLOY_HOST }}:${{ env.APP_PATH }}/

      - name: Restart services
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd ${{ env.APP_PATH }}
            docker compose up -d --build
```

既存の `ci.yml`（構文チェック・フロントビルド）はそのまま残す。`deploy.yml` は独立したワークフローとして追加し、push トリガーが被っても両方走る（他リポと同じ構成）。

### 前提条件（このリポ固有の確認事項）

- GitHub Secrets に `TS_OAUTH_CLIENT_ID` / `TS_OAUTH_SECRET` / `SSH_PRIVATE_KEY` / `DEPLOY_HOST` / `DEPLOY_USER` が設定済みであること（他リポで使っているものと共通の可能性が高いが、本リポの Secrets に登録されているか要確認）
- SV6 上に `.env` が既に配置されていること（`rsync` は `.env` を除外するため、初回は手動配置が前提）

### 確認手順

- push 後、GitHub Actions の `Deploy` ワークフローが成功する
- SSH 先で `docker compose ps` のコンテナ起動時刻が更新されている
- 公開ドメインからアクセスし、フロントの変更（例: 直近の SearchTab.tsx 変更）が反映されていることを確認する
