# https://docs.astral.sh/uv/guides/integration/aws-lambda/
FROM ghcr.io/astral-sh/uv:0.6.16 AS uv

FROM public.ecr.aws/lambda/python:3.13 AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_INSTALLER_METADATA=1
ENV UV_LINK_MODE=copy

RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv export --frozen --no-emit-workspace --no-dev --no-editable -o requirements.txt && \
    uv pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# GenTextLambda
FROM public.ecr.aws/lambda/python:3.13 AS gen-text

COPY --from=builder ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}
COPY ../src/gen_text ${LAMBDA_TASK_ROOT}/src/gen_text/
COPY ../src/shared ${LAMBDA_TASK_ROOT}/src/shared/

CMD [ "src.gen_text.handler.handler" ]

# GenImgLambda
FROM public.ecr.aws/lambda/python:3.13 AS gen-img

COPY --from=builder ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}
COPY ../src/gen_img ${LAMBDA_TASK_ROOT}/src/gen_img/
COPY ../src/shared ${LAMBDA_TASK_ROOT}/src/shared/

CMD [ "src.gen_img.handler.handler" ]

# EditImgLambda
FROM public.ecr.aws/lambda/python:3.13 AS edit-img

COPY --from=builder ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}
COPY ../src/edit_img ${LAMBDA_TASK_ROOT}/src/edit_img/
COPY ../src/shared ${LAMBDA_TASK_ROOT}/src/shared/

CMD [ "src.edit_img.handler.handler" ]

# PubImgLambda
FROM public.ecr.aws/lambda/python:3.13 AS pub-img

COPY --from=builder ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}
COPY ../src/pub_img ${LAMBDA_TASK_ROOT}/src/pub_img/
COPY ../src/shared ${LAMBDA_TASK_ROOT}/src/shared/

CMD [ "src.pub_img.handler.handler" ]