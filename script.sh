#!/bin/bash

command="scp /app/hello.java username@ip:/home/ && sudo docker cp /app/hello.java java-container:/home/ && java /home/hello.java"
output=`sshpass -p password ssh -t username@ip ${command}`