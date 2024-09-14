from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
app = Flask(__name__)
CORS(app)

language_options = [
    {
        "language_name": "Java",
        "language_id": 1
    },
    {
        "language_name": "Python",
        "language_id": 2
    }
]

@app.route('/execute', methods=['POST'])
def execute():
    data = request.get_json()
    language_name = data["language_name"]
    code = data["code"]
    input = data["input"]

    output = ""
    response = ""
    
    with open("/home/codes/input.txt", "w") as f:
        f.write(input)

    if language_name == "Java":
        with open("/home/codes/Solution.java", "w") as f:
            f.write(code)
        
        output = subprocess.run(["./java-execute.sh"], capture_output=True, text=True)
    else:
        with open("/home/codes/solution.py", "w") as f:
            f.write(code)
        
        output = subprocess.run(["./python-execute.sh"], capture_output=True, text=True)
    
    print("Output: ",output.stdout)
    print("Error: ", output.stderr)
    if(len(output.stderr) > len(output.stdout)):
        response = output.stderr
    else:
        response = output.stdout
    
    response = output.strip()
    
    return jsonify(response)

#api to fetch all supported languages, language_id param to be used as peimary key for testcases
@app.route('/get-language-options', methods=["GET"])
def get_language_options():
    return jsonify(language_options), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
