from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import os
app = Flask(__name__)
CORS(app)

def execute_java_code(code, input):
    with open("./codes/Solution.java", "w") as f:
        f.write(code)
    
    with open("./codes/input.txt", "w") as f:
        f.write(input)

    output = subprocess.run(["./script.sh"], capture_output=True, text=True)
    print(output.stdout)
    print(output.stderr)
    if(len(output.stderr) > len(output.stdout)):
        return output.stderr
    else:
        return output.stdout
    

def execute_query(query):
    with open("input.sql", "w") as f:
        f.write(query)
    
    output = subprocess.run(["./script.sh"], capture_output=True, text=True)
    print(output.stdout)

@app.route('/execute', methods=['POST'])
def execute():
    data = request.get_json()
    code = data["code"]
    input = data["input"]
    # java_code = request.data.decode('utf-8')
    output = execute_java_code(code, input).strip()
    return jsonify(output)

    # query = request.data.decode("utf-8")
    # output = execute_query(query)
    # return jsonify(output)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
