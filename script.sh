#!/bin/bash

sshpass -p password scp -o StrictHostKeyChecking=no /app/Solution.java anurag@ip:/home/anurag/
command="echo password | sudo -S docker cp /home/anurag/Solution.java java-container:/home/ > /dev/null 2>/dev/null && echo password | sudo -S docker exec -i java-container java /home/Solution.java > /home/anurag/output.txt 2>/dev/null && cat /home/anurag/output.txt"

output=`sshpass -p password ssh -o StrictHostKeyChecking=no -t anurag@ip ${command}`

echo $output