from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.post("/console/execute-query")
def execute_query():
    data = request.get_json()
    output = os.system("./execute-query.sh "+data['query'])
    return output

if __name__ == "__main__":
    app.run(debug=True)