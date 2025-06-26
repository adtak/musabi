# Musabi

Musabi は、AI を使ってレシピの生成・画像生成・画像編集・SNS 投稿を自動化するシステムです。AWS Step Functions を使用してワークフローを構築し、Lambda 関数と Container で各ステップを実行します。

## 🏗️ アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                     AWS Step Functions                         │
├─────────────────────────────────────────────────────────────────┤
│  GenText  →  GenImg  →  EditImg  →  PubImg                     │
│     ↓         ↓         ↓          ↓                          │
│  OpenAI    DALL-E 3   画像編集     SNS投稿                     │
│  GPT-4       /        タイトル      (Meta)                     │
│           Stable      追加                                     │
│           Diffusion                                            │
└─────────────────────────────────────────────────────────────────┘
                               ↓
                          S3 Bucket
                      (画像・データ保存)
```

## 📁 プロジェクト構成

### コア コンポーネント

- **`lambda/`** - AWS Lambda 関数のソースコード
  - `gen_text/` - OpenAI GPT-4 を使用してレシピテキストを生成
  - `gen_img/` - DALL-E 3 / Google Gemini を使用して料理画像を生成
  - `edit_img/` - 生成された画像にタイトルやスタイルを追加
  - `pub_img/` - 完成した画像とレシピを SNS に投稿
  - `shared/` - 共通ユーティリティ（S3、ロギング、設定管理）

- **`iac-v2/`** - AWS CDK v2 (TypeScript) によるインフラ構築
  - Step Functions、Lambda、ECR、S3 の設定
  - 12 時間ごとのスケジュール実行設定
  - セキュリティとアクセス管理

- **`ml-v2/`** - Stable Diffusion を使用した画像生成
  - SageMaker 処理ジョブ用のコンテナ
  - カスタム画像生成とスタイル適用

- **`util/`** - 画像・音声・動画処理のユーティリティ
  - 画像処理、音声処理、動画生成機能

- **`iac-v1/` & `ml-v1/`** - レガシーコンポーネント (Python CDK)

## 🔄 ワークフロー

Step Functions で以下の順序で自動実行されます：

1. **GenText** - OpenAI GPT-4 で独創的なレシピを生成
2. **GenImg** - DALL-E 3 または Stable Diffusion で料理画像を生成
3. **EditImg** - 画像にタイトルとスタイリングを追加
4. **PubImg** - 完成したコンテンツを SNS (Meta) に投稿

## 🛠️ 技術スタック

### バックエンド
- **Language**: Python 3.13, TypeScript
- **Dependency Management**: uv (Python), npm (Node.js)
- **APIs**: OpenAI (GPT-4, DALL-E 3), Google Gemini
- **Cloud**: AWS (Lambda, Step Functions, S3, ECR, SageMaker)

### インフラ
- **Infrastructure as Code**: AWS CDK v2
- **Container**: Docker, Amazon ECR
- **Orchestration**: AWS Step Functions
- **Storage**: Amazon S3
- **Scheduling**: Amazon EventBridge

### 機械学習
- **Frameworks**: PyTorch, Diffusers
- **Models**: Stable Diffusion, DALL-E 3, GPT-4
- **Image Processing**: Pillow (PIL)

## 🚀 セットアップ

### 前提条件

- Python 3.13+
- Node.js 18+
- AWS CLI と認証設定
- Docker (ml-v2 コンポーネント用)
- uv (Python dependency manager)

### インストール

1. **リポジトリのクローン**
   ```bash
   git clone https://github.com/adtak/musabi.git
   cd musabi
   ```

2. **Lambda 関数の依存関係をインストール**
   ```bash
   cd lambda
   uv sync
   ```

3. **インフラ (CDK) の依存関係をインストール**
   ```bash
   cd iac-v2
   npm install
   ```

4. **機械学習コンポーネントの依存関係をインストール**
   ```bash
   cd ml-v2
   poetry install
   ```

### 設定

#### AWS SSM パラメータ

以下のパラメータを AWS Systems Manager Parameter Store に設定してください：

```bash
# OpenAI API キー
aws ssm put-parameter --name "/openai/musabi/api-key" --value "your-openai-api-key" --type "SecureString"

# Meta (SNS) 認証情報
aws ssm put-parameter --name "/meta/musabi/access-token" --value "your-meta-access-token" --type "SecureString"
aws ssm put-parameter --name "/meta/musabi/page-id" --value "your-meta-page-id" --type "String"
```

#### 環境変数

- `BUCKET_NAME`: S3 バケット名 (edit_img, pub_img で使用)
- `IMAGE_BUCKET`: 画像保存用 S3 バケット
- `PROMPT`, `NEGATIVE_PROMPT`: ml-v2 での画像生成パラメータ

## 🔧 開発コマンド

### Lambda 関数 (`lambda/`)

```bash
# コードフォーマット
make format

# 型チェック
make mypy

# テスト実行
make test

# 全ての品質チェック
make format && make mypy && make test
```

### インフラ (`iac-v2/`)

```bash
# TypeScript ビルド
npm run build

# リント & フォーマット
npm run lint
npm run fmt

# テスト
npm test

# CDK デプロイ
make deploy
```

### 機械学習 (`ml-v2/`)

```bash
# フォーマット
make format

# 型チェック
make mypy

# テスト
make test

# Docker ビルド & デプロイ
make deploy
```

## 🚀 デプロイ

### 1. ECR リポジトリの作成
```bash
cd iac-v2
make deploy-ecr
```

### 2. Lambda コンテナイメージのビルドとプッシュ
```bash
cd lambda
./deploy.sh
```

### 3. Step Functions とインフラのデプロイ
```bash
cd iac-v2
make deploy
```

### 4. 機械学習コンポーネントのデプロイ
```bash
cd ml-v2
make deploy
```

## ⚙️ 設定オプション  

### レシピ生成設定
- モデル: GPT-4.1
- Temperature: 0.8 (創造性を高める)
- Top-p: 0.8
- Frequency/Presence penalty: 0.5/0.8 (多様性を促進)

### 画像生成設定
- DALL-E 3: 高品質な料理画像生成
- Stable Diffusion: カスタムスタイル適用
- 解像度: 1024x1024 (デフォルト)

### スケジュール
- 実行頻度: 12時間ごと
- EventBridge ルールで自動トリガー

## 📊 監視とログ

- **CloudWatch Logs**: 各 Lambda 関数のログ
- **Step Functions**: ワークフロー実行状況の可視化
- **X-Ray**: 分散トレーシング (有効化された場合)

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

### 開発ガイドライン

- **コードスタイル**: Black (Python), Biome (TypeScript)
- **型チェック**: mypy (Python), TypeScript
- **テスト**: pytest (Python), Jest (TypeScript)
- **コミットメッセージ**: Conventional Commits 形式を推奨

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

## 🐛 トラブルシューティング

### よくある問題

1. **OpenAI API エラー**
   - API キーが正しく設定されているか確認
   - レート制限に達していないか確認

2. **AWS 権限エラー**
   - IAM ロールに必要な権限があるか確認
   - SSM パラメータへのアクセス権限を確認

3. **Docker ビルドエラー**
   - Docker デーモンが起動しているか確認
   - ECR リポジトリが作成されているか確認

### デバッグ

```bash
# Lambda 関数のローカル実行
cd lambda/src/gen_text
python handler.py

# Step Functions の実行ログ確認
aws logs describe-log-groups --log-group-name-prefix "/aws/stepfunctions/"
```

## 📞 サポート

質問や問題がある場合は、GitHub Issues でお気軽にお問い合わせください。

---

**Musabi** - AI-Powered Recipe & Content Creation System