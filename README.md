# Musabi

Musabi は、AI を使ってレシピの生成・画像生成・画像編集・SNS 投稿を自動化するシステムです。AWS Step Functions を使用してワークフローを構築し、Lambda 関数と Container で各ステップを実行します。

## 📁 プロジェクト構成

### コア コンポーネント

- **`lambda/`** - AWS Lambda 関数のソースコード

  - `gen_text/` - LLM を使用してレシピテキストを生成
  - `gen_img/` - LLM を使用して料理画像を生成
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

1. **GenText** - LLM でレシピを生成
2. **GenImg** - LLM で料理画像を生成
3. **EditImg** - 画像にタイトルとスタイリングを追加
4. **PubImg** - 完成したコンテンツを SNS に投稿

## 🛠️ 技術スタック

### バックエンド

- **Language**: Python 3.13, TypeScript
- **Dependency Management**: uv (Python)
- **APIs**: OpenAI, Google Gemini
- **Cloud**: AWS (Lambda)

### インフラ

- **Infrastructure as Code**: AWS CDK v2
- **Container**: Docker, Amazon ECR
- **Orchestration**: AWS Step Functions
- **Storage**: Amazon S3
- **Scheduling**: Amazon EventBridge

### 機械学習

- **Frameworks**: PyTorch, Diffusers
- **Models**: Stable Diffusion

## 🚀 GitHub Actions CD Setup

### セットアップ手順

#### 1. GitHub Secrets の設定

以下のシークレットを GitHub リポジトリに設定：

```
AWS_ROLE_ARN: arn:aws:iam::YOUR_ACCOUNT_ID:role/MusabiGitHubActionsRole
```

#### 2. AWS IAM ロールの作成

GitHub Actions が AWS リソースにアクセスするための IAM ロールを作成します：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/musabi:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

#### 3. IAM ロールポリシーの設定

以下のポリシーを IAM ロールにアタッチします：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "arn:aws:ecr:ap-northeast-1:YOUR_ACCOUNT_ID:repository/musabi-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode",
        "lambda:GetFunction",
        "lambda:PublishVersion"
      ],
      "Resource": [
        "arn:aws:lambda:ap-northeast-1:YOUR_ACCOUNT_ID:function:GenTextLambda",
        "arn:aws:lambda:ap-northeast-1:YOUR_ACCOUNT_ID:function:GenImgLambda",
        "arn:aws:lambda:ap-northeast-1:YOUR_ACCOUNT_ID:function:EditImgLambda",
        "arn:aws:lambda:ap-northeast-1:YOUR_ACCOUNT_ID:function:PubImgLambda"
      ]
    }
  ]
}
```

#### 4. GitHub OIDC プロバイダーの設定

AWS IAM コンソールで OIDC プロバイダーを作成します：

- プロバイダー URL: `https://token.actions.githubusercontent.com`
- 対象者: `sts.amazonaws.com`

---

**Musabi** - AI-Powered Recipe & Content Creation System
