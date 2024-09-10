from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import os
import docker
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

def execute_java_code(code, input):
    with open("./codes/Solution.java", "w") as f:
        f.write(code)
    
    with open("./codes/input.txt", "w") as f:
        f.write(input)

    output = subprocess.run(["./script.sh"], capture_output=True, text=True)
    print("Output: ",output.stdout)
    print("Error: ", output.stderr)
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

#Logic for calling through docker
client = docker.from_env()

@app.route('/execute_code_docker', methods=['POST'])
def execute_code():
    data = request.json
    container_id = "239d386b5caa8fd0154b0830f31571c14acb024d240b23aa59a2ee980e272ff4"
    code = data["code"]
    language = data["language"].lower()
    user_input = data.get("input", "")

    if not container_id or not language or not code:
        return jsonify({"error": "language, code, and input are required"}), 400

    try:
        container = client.containers.get(container_id)

        if language == 'python':
            local_file_path = "./codes/app.py"
            container_file_path = "/app.py"

            with open(local_file_path, "w") as f:
                f.write(code)
            with open("./codes/input.txt", "w") as f:
                f.write(user_input)
            
            subprocess.run(['docker', 'cp', local_file_path, f'{container_id}:{container_file_path}'], check=True)
            subprocess.run(['docker', 'cp', "./codes/input.txt", f'{container_id}:{"/input.txt"}'], check=True)

            exec_cmd = f'python app.py < input.txt'
            result = container.exec_run(
                ['sh', '-c', exec_cmd],
                stdout=True,
                stderr=True
            )
            return jsonify({"output": result.output.decode('utf-8')}), 200

        elif language == 'java':
            # Write Java code to a file on the host machine containing compilers
            local_file_path = "./codes/Solution.java"
            container_file_path = "/Solution.java"
            with open(local_file_path, "w") as f:
                f.write(code)
            with open("./codes/input.txt", "w") as f:
                f.write(user_input)

            # Copy the Java file to the container on the host machine containing compilers
            subprocess.run(['docker', 'cp', local_file_path, f'{container_id}:{container_file_path}'], check=True)
            subprocess.run(['docker', 'cp', "./codes/input.txt", f'{container_id}:{"/input.txt"}'], check=True)

            # Compile the Java file inside the container and pass the input
            exec_cmd = f'javac Solution.java && java Solution < input.txt'
            result = container.exec_run(['sh', '-c', exec_cmd], stdin=True, stdout=True, stderr=True)
            # if compile_result.exit_code != 0:
            #     return jsonify({"error": compile_result.output.decode('utf-8')}), 500

            # # Run the compiled Java program with input piped directly
            # command = f'echo "{user_input}" | java Main'
            # result = container.exec_run(['sh', '-c', command], stdin=True, tty=True)

            return jsonify({"output": result.output.decode('utf-8')}), 200

        else:
            return jsonify({"error": "Unsupported language"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


#api to fetch all supported languages, language_id param to be used as peimary key for testcases
@app.route('/get_language_options', methods=["GET"])
def get_language_options():
    return jsonify(language_options), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
