#!/bin/bash

docker stop feast-smart
docker rm feast-smart

docker rmi feast-smart
docker build -t feast-smart -f dockerfile .

docker run -d -p 127.0.0.1:4244:8000 --name feast-smart feast-smart
