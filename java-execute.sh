#!/bin/bash

# sshpass -p password scp -o StrictHostKeyChecking=no /app/Solution.java anurag@ip:/home/anurag/

command="echo password | sudo -S docker cp /home/anurag/codes/Solution.java code-exec-container:/home/ > /dev/null 2>/dev/null && echo password | sudo -S docker exec -i code-exec-container java /home/Solution.java < /home/anurag/codes/input.txt > /home/anurag/codes/output.txt && cat /home/anurag/codes/output.txt"

# sshpass -p password scp -o StrictHostKeyChecking=no /app/input.sql anurag@ip:/home/anurag/

# command="echo password | sudo -S docker cp /home/anurag/input.sql pg-container:/home/ > /dev/null 2>/dev/null && echo password | sudo -S docker exec -i pg-container psql -U postgres -d postgres < input.sql > /home/anurag/output.txt 2>/dev/null && cat output.txt"

output=`sshpass -p password ssh -q -o StrictHostKeyChecking=no -t anurag@ip ${command}`

echo $output