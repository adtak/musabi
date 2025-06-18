# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

Musabi は、AI を使ってレシピの生成・画像生成・画像編集・SNS 投稿を自動化するシステムです。AWS Step Functions を使用してワークフローを構築し、Lambda 関数と Container で各ステップを実行します。

## アーキテクチャ

### 主要コンポーネント

1. **lambda/**: 各種 Lambda 関数のソースコード

   - `gen_text/`: OpenAI API を使用してレシピテキストを生成
   - `gen_img/`: DALL-E 3 を使用して料理画像を生成
   - `edit_img/`: 生成された画像にタイトルやスタイルを追加
   - `pub_img/`: 完成した画像とレシピを SNS に投稿

2. **iac-v2/**: AWS CDK を使用したインフラ構築（TypeScript）

   - Step Functions、Lambda、ECR、S3 の設定
   - 12 時間ごとのスケジュール実行設定

3. **ml-v2/**: Stable Diffusion を使用した画像生成（SageMaker 処理ジョブ用）

4. **iac-v1/**: 旧バージョンのインフラ（Python CDK）

5. **util/**: 画像・音声・動画処理のユーティリティ

### ワークフロー

Step Functions で以下の順序で実行：

1. GenText → レシピ生成
2. GenImg → 画像生成
3. EditImg → 画像編集（タイトル追加）
4. PubImg → SNS 投稿

## 開発コマンド

### Lambda 関数 (lambda/)

```bash
# コードフォーマット
make format

# 型チェック
make mypy

# テスト実行
make test
```

### インフラ（iac-v2/）

```bash
# TypeScriptビルド
npm run build

# CDKデプロイ
make deploy

# リント
npm run lint

# フォーマット
npm run fmt

# テスト
npm test
```

### 機械学習（ml-v2/）

```bash
# フォーマット
make format

# 型チェック
make mypy

# テスト
make test

# Dockerビルド・デプロイ
make deploy
```

### インフラ（iac-v1/） - Python CDK

```bash
# デプロイ
make deploy

# フォーマット
make format

# テスト
make test
```

## 技術スタック

- **Lambda**: Python 3.13 (uv), TypeScript
- **インフラ**: AWS CDK v2 (TypeScript/Python)
- **機械学習**: PyTorch, Diffusers, Stable Diffusion
- **画像処理**: Pillow
- **API**: OpenAI (GPT-4, DALL-E 3)
- **コンテナ**: Docker, ECR
- **ストレージ**: S3
- **オーケストレーション**: Step Functions

## 重要な設定

### 環境変数

- `BUCKET_NAME`: S3 バケット名（edit_img, pub_img）
- `IMAGE_BUCKET`: 画像保存用 S3 バケット
- `PROMPT`, `NEGATIVE_PROMPT`: ml-v2 での画像生成パラメータ

### SSM パラメータ

- `/openai/musabi/api-key`: OpenAI API キー
- `/meta/musabi/*`: SNS 投稿用認証情報

## 依存関係管理

- Lambda: `uv` (Python 3.13)
- iac-v2: `npm` (Node.js/TypeScript)
- ml-v2: `poetry` (Python 3.11)
- iac-v1: `poetry` (Python)
