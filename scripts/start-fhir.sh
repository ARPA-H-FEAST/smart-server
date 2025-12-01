#!/bin/bash

# if [ -z $DATA_DIR ]; then
#     echo This script requires a DATA_DIR to be prvided, aborting
#     exit 0
# fi

# docker run -d -p 8080:8080 --network fhir-backplane \
#     --name fhir-server --volume $DATA_DIR:/app/ feast-hapi-fhir-jpa-starter

MODE="${MODE:-"dev"}"
echo $MODE

if [ $MODE == "dev" ]; then
    echo Running FHIR server in dev mode
    docker run -d -p 8080:8080 --network fhir-backplane \
        --name fhir-server hapi-fhir-server:bitnami-tomcat-memDB
elif [ $MODE == "prod" ]; then
    echo Running FHIR server in PRODUCTION mode
    docker run -d -p 4243:8080 --network fhir-backplane --restart always \
        --name fhir-server -v /data/arpah/dockerdb/:/data/arpah/db/ hapi-fhir-server:bitnami-tomcat-memDB
fi
