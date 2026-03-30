#!/bin/bash

for thread_id in $(seq 1 12); do
    echo Launching thread $thread_id
    # python populate_gwdc2_fhir_fields.py -i $thread_id -d &
    python populate_gwdc2_fhir_fields.py -i $thread_id > /dev/null 2>&1 &
    sleep 1
done
