# 使用官方 Python 運行時作為父鏡像
FROM python:3.10-slim

# 設置工作目錄
WORKDIR /app

# 複製項目文件
COPY . .

# 安裝依賴
RUN pip install -r requirements.txt

# 設置環境變量
ENV PORT=8080
ENV LINE_CHANNEL_SECRET=${LINE_CHANNEL_SECRET}
ENV LINE_CHANNEL_ACCESS_TOKEN=${LINE_CHANNEL_ACCESS_TOKEN}
ENV YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
ENV SERPAPI_API_KEY=${SERPAPI_API_KEY}
ENV OPENAI_API_KEY=${OPENAI_API_KEY}

# 運行應用
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
