#!/bin/bash

MODE="${MODE:-"dev"}"

if [ $MODE == "dev" ]; then
    docker run -d -e POSTGRES_PASSWORD=fhir -e POSTGRES_USER=postgres \
        -e POSTGRES_DB=fhir -v $PWD/fhir-data:/var/lib/postgresql/18/docker \
        --network fhir-backplane -p 5432:5432 --restart always \
        --name db-fhir postgres:18.0-alpine3.22
elif [ $MODE == "prod" ]; then
    echo Running FHIR server in PRODUCTION mode
    docker run -d -e POSTGRES_PASSWORD=fhir -e POSTGRES_USER=postgres \
        -e POSTGRES_DB=fhir -v /data/arpah/imported/dockerdb:/var/lib/postgresql/18/docker \
        --network fhir-backplane --restart always \
        --name db-fhir postgres:18.0-alpine3.22
fi