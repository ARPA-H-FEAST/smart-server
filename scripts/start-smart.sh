#!/bin/bash

if [ -z $MODE ]; then
    echo MODE not defined, aborting
    exit 1
fi

if [ $MODE = "dev" ]; then
    pushd .. > /dev/null 2>&1 
    docker run -d -p 8000:8000 --network fhir-backplane --restart always \
        --name smart-server --volume $(pwd)/datadir/processed/:/data/arpah/processed/ \
        feast-smart
    popd > /dev/null 2>&1 
    exit 0
fi
if [ $MODE = "prod" ]; then
    pushd .. > /dev/null 2>&1 
    docker run -d -p 4244:8000 --network fhir-backplane --restart always \
        --name smart-server --volume /data/arpah/:/data/arpah/ feast-smart
    popd > /dev/null 2>&1 
    exit 0
fi
echo Invalid mode detected, aborting
exit 1
