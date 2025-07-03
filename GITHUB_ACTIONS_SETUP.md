# GitHub Actions CD Setup Guide

このガイドでは、GitHubActionsを使用してAWS ECRとLambda関数の自動デプロイを設定する方法を説明します。

## 前提条件

- AWS アカウントとECRリポジトリが作成済み
- Lambda関数が作成済み
- GitHub リポジトリの管理者権限

## セットアップ手順

### 1. GitHub Secretsの設定

以下のシークレットをGitHubリポジトリに設定してください：

```
AWS_ROLE_ARN: arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActionsRole
```

### 2. AWS IAMロールの作成

GitHub ActionsがAWSリソースにアクセスするためのIAMロールを作成します：

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
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/musabi:*"
        }
      }
    }
  ]
}
```

### 3. IAMロールポリシーの設定

以下のポリシーをIAMロールにアタッチします：

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
      "Resource": "*"
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

### 4. GitHub OIDC プロバイダーの設定

AWS IAMコンソールでOIDCプロバイダーを作成します：

- プロバイダーURL: `https://token.actions.githubusercontent.com`
- 対象者: `sts.amazonaws.com`

### 5. ワークフローファイルの配置

`deploy.yml`ファイルを以下のパスに配置してください：

```
.github/workflows/deploy.yml
```

## 使用方法

### 手動デプロイの実行

1. GitHubリポジトリの「Actions」タブに移動
2. 「Deploy to AWS」ワークフローを選択
3. 「Run workflow」ボタンをクリック
4. デプロイオプションを選択：
   - Environment: production または staging
   - Functions: 特定の関数名（カンマ区切り）または "all"
5. 「Run workflow」を実行

### デプロイ対象の関数

- `gen-text`: GenTextLambda
- `gen-img`: GenImgLambda  
- `edit-img`: EditImgLambda
- `pub-img`: PubImgLambda

## トラブルシューティング

### ECRログインエラー

```
Error: Cannot perform an interactive login from a non TTY device
```

→ AWS credentialsが正しく設定されているか確認してください

### Lambda関数更新エラー

```
Error: Function not found
```

→ Lambda関数名が正しく設定されているか確認してください

### Docker buildエラー

```
Error: failed to solve: target stage "gen_text" not found
```

→ Dockerfileのtarget名にハイフン（-）ではなくアンダースコア（_）を使用してください

## 注意事項

- このワークフローは手動実行のみをサポートしています
- 本番環境へのデプロイは慎重に行ってください
- デプロイ前に必ずテストを実行してください