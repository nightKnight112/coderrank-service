from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import os
app = Flask(__name__)
CORS(app)

def execute_java_code(code):
    """Executes Java code using subprocess and returns the output."""
    with open("Solution.java", "w") as f:
        f.write(code)
    
    output = subprocess.run(["./script.sh"])
    return output

    # try:
    #     subprocess.run(["javac", "Solution.java"], check=True)
    #     output = subprocess.check_output(["java", "Solution"], text=True)
    #     return output
    # except subprocess.CalledProcessError as e:
    #     return str(e)
    # finally:
    #     # Clean up temporary files
    #     os.remove("Solution.java")
    #     # try:
    #     #     os.remove("Solution.class")
    #     # except FileNotFoundError:
    #     #     pass

    # with open('/shared/Solution.java', 'w') as file:
    #     file.write(code)
    



@app.route('/execute', methods=['POST'])
def execute():
    java_code = request.data.decode('utf-8')
    output = execute_java_code(java_code)
    return jsonify({'output': output})

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)