#!/bin/bash

docker run --restart always -d --name feast-fhir-internal-server --network smart-net hapi-fhir-api-server
