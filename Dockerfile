FROM python:3.11-slim

WORKDIR /app

# パッケージリストコピー
COPY requirements.txt /app/

# pip アップグレードとライブラリインストール
# ここでnumpy→pandasの順番でインストールする
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir numpy==1.23.5 && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

