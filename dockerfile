# docker build -t feast-smart -f dockerfile .
FROM feast-smart-base

COPY ./ /server
WORKDIR /server

CMD ["gunicorn", "-c", "gunicorn_conf.py"]
# CMD [ "python", "manage.py", "runserver", "0.0.0.0:8000" ]
