FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN apt update && apt install -y sshpass

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir codes

RUN chmod 777 ./java-execute.sh

RUN chmod 777 ./python-execute.sh

CMD [ "python", "./app.py" ]

EXPOSE 5000