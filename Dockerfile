FROM python:3.9
LABEL authors="tanujralli97@gmail.com"
LABEL maintainers="tanujralli97@gmail.com"

ENV PYTHONUNBUFFERED 1

COPY ./application /application

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt
RUN rm -rf /tmp

WORKDIR /application
