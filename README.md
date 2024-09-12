# coderrank-service

Build:

```docker build --no-cache -t coderrank-service:v1 .```

Run:

```docker run --network=host -itd -v /home/anurag/coderrank-query-execution-service/:/app -p 5000:5000 coderrank-service:v1```
