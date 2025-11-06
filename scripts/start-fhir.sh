#!/bin/bash

# if [ -z $DATA_DIR ]; then
#     echo This script requires a DATA_DIR to be prvided, aborting
#     exit 0
# fi

# docker run -d -p 8080:8080 --network fhir-backplane \
#     --name fhir-server --volume $DATA_DIR:/app/ feast-hapi-fhir-jpa-starter


# NB: Volume mount doesn't work with the gcr container provided by the HAPI FHIR
# folks. Persistence *does* work as long as the container persists, but this is not
# ideal
docker run -d -p 8080:8080 --network fhir-backplane \
    --name fhir-server feast-hapi-fhir-jpa-starter
