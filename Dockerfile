FROM python:3.11-slim AS base
LABEL authors="wwfyde"


ENV TZ=Asia/Shanghai
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY app/ /app/app

COPY main.py /app

COPY .env /app
COPY .env.prod.local /app/.env.prod
COPY pyproject.toml /app

# 安装依赖
RUN pip config set global.index-url https://mirror.sjtu.edu.cn/pypi/web/simple  && pip install pipx && pipx install poetry && poetry config virtualenvs.create false && poetry install --with main
EXPOSE 9112

ENTRYPOINT ["uvicorn", "main:app", "--port", "9112"]