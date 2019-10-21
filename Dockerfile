FROM python:3.7-alpine
RUN apk update
RUN apk add py-pip
RUN adduser -D -u 1001 -s /bin/sh ctfd-discord

ENV TOKEN "token"
ENV DB_URI "mysql+pymysql://root:ctfd@db/ctfd"

WORKDIR /opt/CTFd-discord

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

USER 1002
CMD ["python", "./main.py"]
