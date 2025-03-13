#!/bin/bash

docker run --restart always -d --name feast-fhir-302 --network smart-net feast-fhir-r3.0.1
