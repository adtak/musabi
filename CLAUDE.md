# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Lambda Functions (Python)
- `make format` - Format code using black and ruff
- `make black` - Run black formatter on src/
- `make ruff` - Run ruff linter with auto-fix
- `make mypy` - Type checking with mypy
- `make test` - Run pytest tests
- Build: `uv sync` for dependency installation

### Infrastructure (TypeScript CDK)
- `npm run build` - Compile TypeScript to JavaScript
- `npm run test` - Run Jest unit tests
- `npm run lint` - Run Biome linter
- `npm run fmt` - Format code with Biome
- `npx cdk deploy` - Deploy stack to AWS
- `npx cdk diff` - Compare deployed vs current state
- `npx cdk synth` - Generate CloudFormation template

### ML/Utility Modules (Poetry)
- `poetry install` - Install dependencies
- `poetry run pytest` - Run tests
- `black`, `ruff`, `mypy` - Linting and type checking

## Architecture

### Project Structure
- **`lambda/`** - AWS Lambda functions (Python 3.13, uv)
- **`iac-v2/`** - Infrastructure as Code (TypeScript CDK)
- **`ml-v2/`** - Machine learning containers (Poetry, Python 3.11)
- **`util/`** - Shared utilities (Poetry, Python 3.11)
- **`iac-v1/` & `ml-v1/`** - Legacy components

### Core Workflow
Step Functions orchestrates Lambda functions in sequence:
1. **GenText** - LLM generates recipe using OpenAI API
2. **GenImg** - LLM generates food image using Google Gemini API
3. **EditImg** - Adds titles and styling to images
4. **PubImg** - Posts content to social media using Meta Graph API

### Lambda Functions
Each function runs in Docker containers with specific dependency groups:
- `gen-text`: Uses OpenAI API (SSM: `/openai/musabi/api-key`)
- `gen-img`: Uses Google Gemini API (SSM: `/google/gemini/musabi/api-key`)
- `edit-img`: Image processing with Pillow
- `pub-img`: Social media posting (SSM: `/meta/musabi/*`)

### Infrastructure Components
- S3 bucket for image storage (`musabi-bucket`)
- ECR repositories for Lambda container images
- EventBridge scheduled execution (every 12 hours at 2:00 and 11:00 UTC)
- IAM policies for SSM parameters and S3 access

### Configuration Management
All API keys stored in AWS SSM Parameter Store:
- OpenAI: `/openai/musabi/api-key`
- Google Gemini: `/google/gemini/musabi/api-key`
- Meta Graph API: `/meta/musabi/*` (access-token, account-id, version, graph-url)

### Development Notes
- Lambda functions use dependency groups in pyproject.toml for modular installs
- TypeScript infrastructure uses Biome for linting/formatting
- ML components use Stable Diffusion and PyTorch
- All Python code follows strict typing with mypy configuration