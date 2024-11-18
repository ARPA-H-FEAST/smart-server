# docker build -t feast-smart-base -f dockerfile.base .
FROM python:3.13.0-slim-bullseye AS feast-smart-base

COPY ./requirements.txt /

ARG DEBIAN_FRONTEND=noninteractive
RUN mkdir -p /var/log/gunicorn/ && \
    mkdir -p /var/run/gunicorn/ && \
    apt update && \
    apt install -y python3-dev curl && \
    pip3 install -r requirements.txt

# docker build -t feast-smart -f dockerfile .
FROM feast-smart-base

COPY ./ /server
WORKDIR /server

# CMD ["gunicorn", "-c", "gunicorn_conf.py"]
CMD [ "python", "manage.py", "runserver", "0.0.0.0:8000" ]
