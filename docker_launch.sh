#!/bin/bash

# wait for docker to respond
for i in $(seq 20); do
    if curl -s http://localhost:5984 > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

gunicorn -w 5 -b :8080 web:server