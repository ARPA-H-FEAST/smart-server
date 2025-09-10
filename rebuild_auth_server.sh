#!/bin/bash

docker cp feast-smart:/server/db.sqlite3 .

docker stop feast-smart
docker rm feast-smart

docker rmi feast-smart
docker build -t feast-smart -f dockerfile .

### TODO / FIXME: Dynamic mount based on local/remote deployment?
docker run --restart always -d -p 127.0.0.1:4244:8000 -v /data/arpah/:/data/arpah/ --network smart-net --name feast-smart feast-smart

