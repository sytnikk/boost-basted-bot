FROM python:3.7-alpine

WORKDIR /usr/src/app

RUN apk add --no-cache \
        ffmpeg \
        build-base \
        libressl-dev \
        gcc \
        musl-dev \
        python3-dev \
        openssl-dev \
        libffi-dev && \
    pip install --no-cache-dir cryptography==2.1.4

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]