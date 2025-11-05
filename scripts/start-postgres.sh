#!/bin/bash

docker run -d -e POSTGRES_PASSWORD=fhir -e POSTGRES_USER=postgres \
    -e POSTGRES_DB=fhir -v $PWD/fhir-data:/var/lib/postgres/data \
    --network fhir-backplane --name db-fhir postgres:18.0-alpine3.22
