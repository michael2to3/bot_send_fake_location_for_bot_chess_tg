FROM python:3.12.0b3-slim
ENV TZ="Europe/Moscow"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./ /app
WORKDIR /app
ENTRYPOINT ["python", "."]
