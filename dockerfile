# docker build -t feast-smart-base -f dockerfile.base .
FROM python:3.13.0-slim-bullseye AS feast-smart-base

COPY ./requirements.txt /

ARG DEBIAN_FRONTEND=noninteractive
RUN mkdir -p /var/log/gunicorn/ && \
    mkdir -p /var/run/gunicorn/ && \
    apt update && \
    apt install -y python3-dev curl dnsutils net-tools && \
    pip3 install -r requirements.txt 

COPY ./ /server
WORKDIR /server

# docker build -t feast-smart -f dockerfile .
FROM feast-smart-base

# Temporarily freeze the DB to preserve application codes
# via copying the database file directly into the container
# Will break if models change & migrations are required
# COPY ./ /server
# WORKDIR /server

# TMP
# RUN python manage.py makemigrations && \
#     cd utilities && bash initialize_db.sh && cd -

# CMD ["gunicorn", "-c", "gunicorn_conf.py"]
CMD [ "python", "manage.py", "runserver", "0.0.0.0:8000" ]
