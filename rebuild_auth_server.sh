#!/bin/bash

docker stop feast-smart
docker rm feast-smart

docker rmi feast-smart
docker build -t feast-smart -f dockerfile .

docker run -d --rm -p 8000:8000 --name feast-smart feast-smart
