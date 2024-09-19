from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import docker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from database_utils.models import LanguageInfo, UserMetadata, UserMaster
import uuid

app = Flask(__name__)
CORS(app)

#Db configuration
DATABASE_URL = "postgresql://postgres:password@localhost:5432/coderrank_db"
db_engine = create_engine(DATABASE_URL)
db_session = sessionmaker(bind=db_engine)
db_session_ac = db_session() #dbSession object


#api to fetch all supported languages, language_id param to be used as primary key for testcases
@app.route('/get-language-options', methods=["GET"])
def get_language_options():
    try:
        languages = db_session_ac.query(LanguageInfo).all()
        return_body = []
        for items in languages:
            temp = {
                "language_name" : items.language_name,
                "language_uuid" : items.language_uuid
            }
            return_body.append(temp)
        return jsonify(return_body), 200
    except Exception as e:
        return jsonify({'error' : e}), 400


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
    
    response = response.strip()
    
    return jsonify(response)

# code execution through docker exec
@app.route('/execute_code_docker', methods=['POST'])
def execute_code():
    client = docker.from_env()
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

            return jsonify({"output": result.output.decode('utf-8')}), 200

        else:
            return jsonify({"error": "Unsupported language"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

#user-end apis
@app.route('/login-user', methods=['POST'])
def user_login():
    data = request.json
    user_alias = data["user_alias"] #username == actual name && user_alias == username given by user, eg:Dedsec Potter, CoderMaster69
    password = data["password"]
    try:
        users = db_session_ac.query(UserMetadata).filter_by(user_alias=user_alias,user_password=password).all()
        user_id = users[0].user_id
        user_master_data = db_session_ac.query(UserMaster).filter_by(user_id=user_id).all()
        user_uuid = user_master_data[0].user_uuid
        if(len(users) == 1):
            return jsonify({'message': 'Logged in successfully', 'user_id' : user_uuid}), 200
        else:
            return jsonify({'message': 'Username or password is incorrect'}), 400
    except Exception as e:
        return jsonify({'message': 'Failed to login user'}), 500

@app.route('/register-user', methods=['POST'])
def user_registration():
    data = request.json
    user_uuid = uuid.uuid4()
    name = data['full_name']
    user_alias = data['user_alias']
    password = data['user_password']
    phone = data['phone_no']
    email = data['email']

    allUsers = db_session_ac.query(UserMaster).all()
    if(len(allUsers) > 0):
        last_given_userid = allUsers[len(allUsers)-1].user_id
        last_given_userid += 1
    else:
        last_given_userid = 1

    new_user_master = UserMaster(
        user_id=last_given_userid,
        user_uuid=user_uuid
    )

    new_user_metadata = UserMetadata(
        user_id=last_given_userid,
        user_name=name,
        user_alias=user_alias,
        user_password=password,
        user_phone_no=phone,
        user_email=email,
        no_of_times_user_login=0,
        no_of_problems_solved=0,
        is_admin=False
    )

    try:
        db_session_ac.add(new_user_master)
        db_session_ac.commit()
        db_session_ac.add(new_user_metadata)
        db_session_ac.commit()
        return jsonify({'message': 'user registered successfully'}), 200
    except Exception as e:
        db_session_ac.rollback()
        return jsonify({'error': e}), 500
    
@app.route('/user-details/', defaults={'user_alias': None}, methods=['GET'])
@app.route('/user-details/<string:user_alias>', methods=['GET'])
def get_user_details(user_alias):

    if user_alias is None:
        userDetails = db_session_ac.query(UserMaster).options(joinedload(UserMaster.user_metadata)).all()
        resBody = []
        for users in userDetails:
            if(users.user_metadata.is_admin == False): #admin user cannot view other admin user data
                temp = {
                    'user_id' : users.user_uuid,
                    'user_metadata' : {
                        "full_name" : users.user_metadata.user_name,
                        "user_alias" : users.user_metadata.user_alias,
                        "user_password" : users.user_metadata.user_password,
                        "phone_no" : users.user_metadata.user_phone_no,
                        "email" : users.user_metadata.user_email,
                        "user_login_count" : users.user_metadata.no_of_times_user_login,
                        "problem_solved_count" : users.user_metadata.no_of_problems_solved
                    }
                }
                resBody.append(temp)

        print(resBody)
        return jsonify(resBody), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
