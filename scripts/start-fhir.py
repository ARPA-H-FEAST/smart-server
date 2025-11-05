#!/bin/bash

docker run -d -p 8080:8080 --network fhir-backplane \
    --name fhir feast-hapi-fhir-jpa-starter
