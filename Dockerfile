FROM python:3

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt


CMD [ "python", "./app.py" ]

EXPOSE 5000