#!/bin/bash
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <docker-compose-file-name> <number-of-clients>"
    exit 1
fi

COMPOSE_FILE=$1
NUM_CLIENTS=$2

if ! [[ "$NUM_CLIENTS" =~ ^[0-9]+$ ]]; then
    echo "Error: <number-of-clients> must be a non-negative integer."
    exit 1
fi

generate_compose_file() {
    echo "name: tp0" > $COMPOSE_FILE
    echo "services:" >> $COMPOSE_FILE
    
    echo "  server:" >> $COMPOSE_FILE
    echo "    container_name: server" >> $COMPOSE_FILE
    echo "    image: server:latest" >> $COMPOSE_FILE
    echo "    entrypoint: python3 /main.py" >> $COMPOSE_FILE
    echo "    volumes:" >> $COMPOSE_FILE
    echo "      - ./server/config.ini:/config.ini" >> $COMPOSE_FILE
    echo "    environment:" >> $COMPOSE_FILE
    echo "      - PYTHONUNBUFFERED=1" >> $COMPOSE_FILE
    echo "      - LOGGING_LEVEL=DEBUG" >> $COMPOSE_FILE
    echo "    networks:" >> $COMPOSE_FILE
    echo "      - testing_net" >> $COMPOSE_FILE
    echo "" >> $COMPOSE_FILE

    for i in $(seq 1 $NUM_CLIENTS); do
        echo "  client$i:" >> $COMPOSE_FILE
        echo "    container_name: client$i" >> $COMPOSE_FILE
        echo "    image: client:latest" >> $COMPOSE_FILE
        echo "    entrypoint: /client" >> $COMPOSE_FILE
        echo "    volumes:" >> $COMPOSE_FILE
        echo "      - ./client/config.yaml:/config.yaml" >> $COMPOSE_FILE
        echo "    environment:" >> $COMPOSE_FILE
        echo "      - CLI_ID=$i" >> $COMPOSE_FILE
        echo "      - CLI_LOG_LEVEL=DEBUG" >> $COMPOSE_FILE
        echo "    networks:" >> $COMPOSE_FILE
        echo "      - testing_net" >> $COMPOSE_FILE
        echo "    depends_on:" >> $COMPOSE_FILE
        echo "      - server" >> $COMPOSE_FILE
        echo "" >> $COMPOSE_FILE
    done

    echo "networks:" >> $COMPOSE_FILE
    echo "  testing_net:" >> $COMPOSE_FILE
    echo "    ipam:" >> $COMPOSE_FILE
    echo "      driver: default" >> $COMPOSE_FILE
    echo "      config:" >> $COMPOSE_FILE
    echo "        - subnet: 172.25.125.0/24" >> $COMPOSE_FILE
}

generate_compose_file

echo "'$COMPOSE_FILE' created successfully with $NUM_CLIENTS client(s)."
