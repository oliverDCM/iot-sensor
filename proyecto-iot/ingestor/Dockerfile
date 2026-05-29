FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY firebase-key.json .
CMD ["python", "main.py"]