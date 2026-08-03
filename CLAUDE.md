# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Lambda Functions (Python, in `lambda/`)

- `make format` - Format code using black and ruff
- `make mypy` - Type checking with mypy
- `make test` - Run pytest tests
- `uv sync --all-groups` - Install all dependencies
- `uv add --group <function-name> package` - Add dependency to a specific function group
- ONLY use `uv`, NEVER `pip`. `uv pip install` and `@latest` syntax are forbidden.

### Infrastructure (TypeScript CDK, in `iac-v2/`)

- `npm run build` - Compile TypeScript
- `npm run test` - Run Jest tests
- `npm run lint` / `npm run fmt` - Biome linter and formatter
- `make synth` - Generate CloudFormation template
- `make deploy-ecr` - Deploy ECR repositories
- `make deploy` - Deploy all stacks

### Docker (Lambda containers)

- Build a single function: `docker build --target <func> --build-arg INSTALL_GROUP=<func> -f lambda/docker/Dockerfile lambda/`
- Valid targets: `gen-text`, `gen-img`, `select-img`, `edit-img`, `pub-img`

## Architecture

### Project Structure

- **`lambda/`** - AWS Lambda functions (Python 3.13, uv). Has its own `CLAUDE.md` with detailed coding guidelines.
- **`iac-v2/`** - Infrastructure as Code (TypeScript CDK v2, Biome)
- **`ml-v2/`** - ML containers for Stable Diffusion (Poetry, Python 3.11)
- **`util/`** - Shared media processing utilities (uv, Python 3.11+)
- **`iac-v1/` & `ml-v1/`** - Legacy components (Python CDK v1)

### Core Workflow

Step Functions orchestrates Lambda functions. Deployed to ap-northeast-1, triggered by EventBridge every 12 hours (2:00 and 11:00 UTC).

1. **GenText** - Generates recipe via OpenAI API (LangChain)
2. **GenImg** - Generates 4 food images **in parallel** via Google Gemini API
3. **SelectImg** - Evaluates and selects the best image via Gemini
4. **EditImg** - Adds titles and styling to the selected image (Pillow)
5. **PubImg** - Posts content to Instagram via Meta Graph API

### Lambda Function Design

- Each function is a Docker container built from a multi-stage Dockerfile (`lambda/docker/Dockerfile`)
- Dependencies are organized as groups in `lambda/pyproject.toml` — one group per function plus a `shared` group
- Shared code in `lambda/src/shared/`: config, logging (loguru), S3 utilities, Pydantic type definitions
- LangSmith tracing integrated in gen-text and gen-img

### SSM Parameter Store Keys

- `/openai/musabi/*` - OpenAI API key
- `/google/gemini/musabi/*` - Google Gemini API key
- `/langsmith/musabi/*` - LangSmith tracing config
- `/meta/musabi/*` - Meta Graph API (access-token, account-id, version, graph-url)

## Git & PR Conventions

- Add `--trailer "Reported-by:<name>"` for bug fixes from user reports
- Add `--trailer "Github-Issue:#<number>"` for issue-related commits
- NEVER mention co-authored-by or the tool used to create commits/PRs
- PR descriptions: focus on the problem being solved and the approach, not code-level details

## CI/CD

- **CI** (`lambda-ci.yml`): Runs on PRs/pushes touching `lambda/` — checks formatting (black, ruff) and types (mypy)
- **CD** (`lambda-cd.yml`): Manual dispatch — builds Docker images, pushes to ECR, updates Lambda functions
- Infrastructure is deployed separately via `npx cdk deploy` from `iac-v2/`
