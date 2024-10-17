# 使用官方 Python 運行時作為父鏡像
FROM python:3.10-slim

# 安裝系統依賴
RUN apt-get update && apt-get install -y libpq-dev gcc

# 設置工作目錄
WORKDIR /app

# # 安裝 poetry
# RUN pip install poetry

# # 複製 pyproject.toml 和 poetry.lock 文件
# COPY pyproject.toml poetry.lock ./

# # 安裝項目依賴
# RUN poetry config virtualenvs.create false \
#   && poetry install --only main --no-interaction --no-ansi
COPY requirements.txt .

RUN pip install -r requirements.txt

# 複製項目文件
COPY . .

# 設置環境變量
ENV PORT=8080
# 設置環境變量
ARG LINE_CHANNEL_SECRET
ARG LINE_CHANNEL_ACCESS_TOKEN
ARG YOUTUBE_API_KEY
ARG SERPAPI_API_KEY
ARG OPENAI_API_KEY

ENV LINE_CHANNEL_SECRET=$LINE_CHANNEL_SECRET
ENV LINE_CHANNEL_ACCESS_TOKEN=$LINE_CHANNEL_ACCESS_TOKEN
ENV YOUTUBE_API_KEY=$YOUTUBE_API_KEY
ENV SERPAPI_API_KEY=$SERPAPI_API_KEY
ENV OPENAI_API_KEY=$OPENAI_API_KEY

# 運行應用
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
