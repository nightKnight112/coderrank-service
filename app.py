from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import os
app = Flask(__name__)
CORS(app)

def execute_java_code(code):
    with open("./codes/Solution.java", "w") as f:
        f.write(code)
    
    output = subprocess.run(["./script.sh"], capture_output=True, text=True)
    print(output.stdout)
    return output.stdout
    

def execute_query(query):
    with open("input.sql", "w") as f:
        f.write(query)
    
    output = subprocess.run(["./script.sh"], capture_output=True, text=True)
    print(output.stdout)
    return output.stdout

@app.route('/execute', methods=['POST'])
def execute():
    java_code = request.data.decode('utf-8')
    output = execute_java_code(java_code).strip()
    return jsonify(output)

    # query = request.data.decode("utf-8")
    # output = execute_query(query)
    # return jsonify(output)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
