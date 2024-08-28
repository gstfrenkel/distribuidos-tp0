#!/bin/bash
NETWORK_NAME="tp0_testing_net"
MESSAGE="Testing echo-server..."
CONFIG_FILE="server/config.ini"
SERVER_IP=$(awk -F' = ' '/SERVER_IP/ {print $2}' $CONFIG_FILE | tr -d '\r')
SERVER_PORT=$(awk -F' = ' '/SERVER_PORT/ {print $2}' $CONFIG_FILE | tr -d '\r')

RESULT=$(docker run --rm --network $NETWORK_NAME busybox sh -c "echo '$MESSAGE' | nc $SERVER_IP $SERVER_PORT")

if [ "$RESULT" == "$MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi
