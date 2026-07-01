## 変更内容

`infrastructure/deploy.sh` は手動実行前提で、main への push が本番（SV6）に自動反映されていなかった。attendance-system-migration / order-system-migration と同じ Tailscale + SSH + `docker compose up -d --build` パターンに揃え、`.github/workflows/deploy.yml` を新規追加した。

- `on.push.branches: [main]` で main への push をトリガー
- `tailscale/github-action@v3` で Tailscale 接続（`tag:ci`）
- SSH 鍵をセットアップし `ssh-keyscan` で known_hosts 登録
- `rsync -az --delete`（`.git` / `node_modules` / `src/web/node_modules` / `.env` を除外）でファイル同期
- `appleboy/ssh-action@v1` でリモート先の `docker compose up -d --build` を実行

既存の `ci.yml`（構文チェック・フロントビルド）はそのまま残し、`deploy.yml` は独立ワークフローとして追加した。push トリガーが被るため両方走る（他リポと同じ構成）。

## 静的確認結果

- `.github/workflows/deploy.yml` を `pyyaml` で `yaml.safe_load` し、YAML として正しくパースできることを確認した（`OK`）
- issue の実装方針に記載された `attendance-system-migration/.github/workflows/deploy.yml` 相当の内容（Tailscale 接続 → SSH セットアップ → rsync 同期 → リモート `docker compose up -d --build`）をそのまま反映していることを確認した
- 参照する Secrets（`TS_OAUTH_CLIENT_ID` / `TS_OAUTH_SECRET` / `SSH_PRIVATE_KEY` / `DEPLOY_HOST` / `DEPLOY_USER`）はワークフロー内で `secrets.*` として参照するのみで、値のハードコードはない
- `rsync` の除外パターン（`.git` / `node_modules` / `src/web/node_modules` / `.env`）は既存の `infrastructure/deploy.sh` と一致していることを確認した
- 既存 `ci.yml` は変更していないため、構文チェック・フロントビルドの CI 挙動に影響しないことを確認した

`git diff --name-only HEAD~1`:
```
.github/workflows/deploy.yml
```

## 検証手順

- GitHub Secrets に `TS_OAUTH_CLIENT_ID` / `TS_OAUTH_SECRET` / `SSH_PRIVATE_KEY` / `DEPLOY_HOST` / `DEPLOY_USER` が本リポに設定済みであることを確認する（未設定なら追加する）
- SV6 上に `.env` が既に配置されていることを確認する（`rsync` は `.env` を除外するため、初回は手動配置が前提）
- main にマージ後、GitHub Actions の `Deploy` ワークフローが成功することを確認する
- SSH 先で `docker compose ps` のコンテナ起動時刻が更新されていることを確認する
- 公開ドメインからアクセスし、フロントの変更（例: 直近の SearchTab.tsx 変更）が反映されていることを確認する
