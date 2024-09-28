from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import subprocess
import docker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from database_utils.models import LanguageInfo, UserMetadata, UserMaster, ProblemStatementMaster, ProblemStatementMetadata, ProblemStatementTestCases
import uuid
from database_utils.dbUtils import user_update_fields, problem_update_fields
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import timedelta
import os
import utils
import requests
import json

app = Flask(__name__)
CORS(app, supports_credentials=True)

environment = os.environ.get("env")
db_username = os.environ.get("db_username")
db_password = os.environ.get("db_password")
vm_ip = os.environ.get("vm_ip")

#Db configuration
DATABASE_URL = f"postgresql://{db_username}:{db_password}@{vm_ip}:5432/coderrank_db"
print(DATABASE_URL)
db_engine = create_engine(DATABASE_URL)
db_session = sessionmaker(bind=db_engine)
db_session_ac = db_session() #dbSession object


# Logging configuration
logging.basicConfig(format="{asctime} - {levelname} - {message}", style="{", datefmt="%Y-%m-%d %H:%M:%S")

# JWT config
jwt = JWTManager(app)
jwt_secret_key = os.popen("openssl rand -hex 32").read()
app.config["JWT_SECRET_KEY"] = jwt_secret_key
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(minutes=5)
app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]
app.config['JWT_COOKIE_CSRF_PROTECT'] = False

#api to fetch all supported languages, language_id param to be used as primary key for testcases
@app.route('/get-language-options', methods=["GET"])
@jwt_required()
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
    
    with open("/home/codes/input.txt", "w") as f:
        f.write(input)

    if language_name == "Java":
        with open("/home/codes/Solution.java", "w") as f:
            f.write(code)
        
        output = requests.request("POST", url=f"http://{vm_ip}:5001/execute", data=json.dumps({"language_name": language_name, "filename": "/home/codes/Solution.java", "input_filename": "/home/codes/input.txt"}), headers={"Content-Type": "application/json"}).json()
    else:
        with open("/home/codes/solution.py", "w") as f:
            f.write(code)
        
        output = requests.request("POST", url=f"http://{vm_ip}:5001/execute", data=json.dumps({"language_name": language_name, "filename": "/home/codes/solution.py", "input_filename": "/home/codes/input.txt"}), headers={"Content-Type": "application/json"}).json()
    
    return jsonify(output)

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
    print(environment, db_username, db_password, vm_ip)
    data = request.json
    user_alias = data["user_alias"] #username == actual name && user_alias == username given by user, eg:Dedsec Potter, CoderMaster69
    password = data["password"]
    try:
        users = db_session_ac.query(UserMetadata).filter_by(user_alias=user_alias).all()
        if users and check_password_hash(users[0].user_password, password):
            user_id = users[0].user_id
            user_master_data = db_session_ac.query(UserMaster).filter_by(user_id=user_id).all()
            user_uuid = user_master_data[0].user_uuid
            is_user_admin = user_master_data[0].user_metadata.is_admin

            users[0].no_of_times_user_login += 1
            db_session_ac.commit()

            access_token = create_access_token(identity=user_alias, additional_claims={"user_uuid": user_uuid})
            refresh_token = create_refresh_token(identity=user_alias, additional_claims={"user_uuid": user_uuid})
            
            response = make_response(jsonify({'message': 'Logged in successfully', 'admin_user' : is_user_admin, "access_token": access_token, "refresh_token": refresh_token}))

            if environment == "local": 
                response.set_cookie("refresh_token_cookie", refresh_token, secure=True, samesite="None", max_age=timedelta(minutes=5))
                response.set_cookie("isLoggedIn", "true", secure=True, samesite="None", max_age=timedelta(minutes=5))
            else:
                response.set_cookie("refresh_token_cookie", refresh_token, httponly=True, max_age=timedelta(minutes=5))
                response.set_cookie("isLoggedIn", "true", max_age=timedelta(minutes=5))
            return response
        else:
            return jsonify({'message': 'Username or password is incorrect'}), 400
    except Exception as e:
        print(e)
        logging.error(e)
        return jsonify({'message': 'Failed to login user'}), 500

@app.route("/renew-token", methods=["POST"])
@jwt_required(refresh=True)
def renew_token():
    identity = get_jwt_identity()
    user_uuid = utils.decode_token(request.cookies["refresh_token_cookie"], jwt_secret_key)["user_uuid"]
    print(user_uuid)
    new_access_token =  create_access_token(identity, additional_claims={"user_uuid": user_uuid})
    return jsonify({"access_token": new_access_token})

@app.route('/register-user', methods=['POST'])
def user_registration():
    data = request.json
    user_uuid = uuid.uuid4()
    name = data['full_name']
    user_alias = data['user_alias']
    password = generate_password_hash(data['user_password'])
    phone = data['phone_no']
    email = data['email']

    users = db_session_ac.query(UserMetadata).filter_by(user_alias=user_alias).all()
    if users:
        return jsonify({"message": "This username already exists, please try a different one"}), 400

    new_user_master = UserMaster(
        user_uuid=user_uuid
    )

    new_user_metadata = UserMetadata(
        user_name=name,
        user_alias=user_alias,
        user_password=password,
        user_phone_no=phone,
        user_email=email,
        no_of_times_user_login=0,
        no_of_problems_solved=0,
        is_admin=False
    )

    new_user_master.user_metadata = new_user_metadata

    try:
        db_session_ac.add(new_user_master)
        db_session_ac.commit()
        return jsonify({'message': 'User registered successfully'}), 200
    except Exception as e:
        db_session_ac.rollback()
        logging.error(e)
        return jsonify({'message': 'Failed to register'}), 500

@app.route('/user-details/', defaults={'user_uuid': None}, methods=['GET'])
@app.route('/user-details/<string:user_uuid>', methods=['GET'])
@jwt_required()
def get_user_details(user_uuid):
    if user_uuid is None:
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

        # print(resBody)
        return jsonify(resBody), 200
    else:
        userDetails = db_session_ac.query(UserMaster).filter_by(user_uuid=user_uuid).first()
        temp = {
                    'user_id' : userDetails.user_uuid,
                    'user_metadata' : {
                        "full_name" : userDetails.user_metadata.user_name,
                        "user_alias" : userDetails.user_metadata.user_alias,
                        "user_password" : userDetails.user_metadata.user_password,
                        "phone_no" : userDetails.user_metadata.user_phone_no,
                        "email" : userDetails.user_metadata.user_email,
                        "user_login_count" : userDetails.user_metadata.no_of_times_user_login,
                        "problem_solved_count" : userDetails.user_metadata.no_of_problems_solved
                    }
                }
        return jsonify(temp), 200

@app.route('/delete-user', methods=['DELETE'])
@jwt_required()
def delete_user():
    data = request.json
    user_to_be_deleted = data['user_to_be_deleted']
    requester_id = data['requester_user_id']

    requestedUser = db_session_ac.query(UserMaster).filter_by(user_uuid=user_to_be_deleted).first()

    if(requester_id == user_to_be_deleted): #user self-delete logic
        try:
            db_session_ac.delete(requestedUser)
            db_session_ac.commit()
            return jsonify({'message': 'user deleted successfully'}), 200
        except Exception as e:
            return jsonify({'message': 'cannot delete user, user does not exist'}), 400
    
    else: #admin deletes user logic
        requesterUser = db_session_ac.query(UserMaster).filter_by(user_uuid=requester_id).first()
        if(requesterUser and requesterUser.user_metadata.is_admin):
            db_session_ac.delete(requestedUser)
            db_session_ac.commit()
            return jsonify({'message': 'user deleted successfully'}), 200
        else:
            return jsonify({'message': 'cannot delete user, user unauthorized or does not exist'}), 400

@app.route('/edit-user', methods=['PUT'])
@jwt_required()
def edit_user():
    data = request.json
    user_to_be_edited = data['user_to_be_edited']
    requester_id = data['requester_user_id']
    edit_metadata = data['edit_metadata']

    requestedUser = db_session_ac.query(UserMaster).filter_by(user_uuid=user_to_be_edited).first()
    requesterUser = db_session_ac.query(UserMaster).filter_by(user_uuid=requester_id).first()

    if(user_to_be_edited == requester_id):
        try:
            flag = True
            for field, model_attr in user_update_fields.items():
                if field in edit_metadata and edit_metadata.get(field) is not None and flag:
                    if(field == "is_admin"):
                        if(requesterUser.user_metadata.is_admin):
                            setattr(requestedUser.user_metadata, model_attr.split('.')[-1], edit_metadata[field])
                        else:
                            flag = False
                    else:
                        setattr(requestedUser.user_metadata, model_attr.split('.')[-1], edit_metadata[field])
            db_session_ac.commit()
            if(flag):
                return jsonify({'message': 'user details edited successfully'}), 200
            else:
                return jsonify({'error': 'privillege escalation attempted'}), 403
        except Exception as e:
            return jsonify({'error': 'user details cannot be edited'}), 400
    else:
        if(requesterUser and requesterUser.user_metadata.is_admin):
            for field, model_attr in user_update_fields.items():
                if field in edit_metadata and edit_metadata.get(field) is not None:
                    setattr(requestedUser.user_metadata, model_attr.split('.')[-1], edit_metadata[field])
            db_session_ac.commit()
            return jsonify({'message': 'user details edited successfully'}), 200
        else:
            return jsonify({'message': 'cannot modify user'}), 400


@app.route("/view-user", methods=["GET"])
@jwt_required()
def view_user():
    print(request.headers)
    return jsonify(1)

# problem end APIs

@app.route('/get-problem-list/',defaults={'problem_id': None}, methods=['GET'])
@app.route('/get-problem-list/<string:problem_id>',  methods=['GET'])
@jwt_required()
def get_problem_list(problem_id):

    if(problem_id):
        allProblemList = []

        allProblemObject = db_session_ac.query(ProblemStatementMaster).filter_by(problem_statement_uuid=problem_id).first()
        allProblemList = [{
            "problem_statement_id" : allProblemObject.problem_statement_uuid,
                "metadata" : {
                    "question" : allProblemObject.problem_statement_metadata.problem_statement_body,
                    "sample_input" : allProblemObject.problem_statement_metadata.sample_input,
                    "sample_output" : allProblemObject.problem_statement_metadata.sample_output,
                    "duration" : allProblemObject.problem_statement_metadata.problem_duration,
                    "hints" : allProblemObject.problem_statement_metadata.problem_hint,
                    "no_of_test_cases" : allProblemObject.problem_statement_metadata.no_of_test_cases
                }
        }]
        return jsonify(allProblemList), 200

    else:
        allProblemList = []

        allProblemObject = db_session_ac.query(ProblemStatementMaster).all()

        for problems in allProblemObject:
            temp = {
                "problem_statement_id" : problems.problem_statement_uuid,
                "metadata" : {
                    "question" : problems.problem_statement_metadata.problem_statement_body,
                    "sample_input" : problems.problem_statement_metadata.sample_input,
                    "sample_output" : problems.problem_statement_metadata.sample_output,
                    "duration" : problems.problem_statement_metadata.problem_duration,
                    "hints" : problems.problem_statement_metadata.problem_hint,
                    "no_of_test_cases" : problems.problem_statement_metadata.no_of_test_cases
                }
            }

            allProblemList.append(temp)
        
        return jsonify(allProblemList), 200

@app.route('/add-problem', methods=['POST'])
@jwt_required()
def add_problem():
    data = request.json
    problem_statement_uuid = uuid.uuid4()
    problem_statement_body = data['statement_body']
    sample_input = data['sample_input']
    sample_output = data['sample_output']
    problem_statement_duration = data['duration']
    problem_hint = data['hint']
    no_of_test_cases = data['no_of_test_cases']

    allProblems = db_session_ac.query(ProblemStatementMaster).all()
    if(len(allProblems) > 0):
        last_given_problem_id = allProblems[len(allProblems)-1].problem_statement_id
        last_given_problem_id += 1
    else:
        last_given_problem_id = 1

    new_problem_statement_master = ProblemStatementMaster(
        problem_statement_id= last_given_problem_id,
        problem_statement_uuid = problem_statement_uuid,
        problem_statement_metadata = ProblemStatementMetadata(
            problem_statement_id = last_given_problem_id,
            problem_statement_body= problem_statement_body,
            sample_input=sample_input,
            sample_output=sample_output,
            problem_duration = problem_statement_duration,
            problem_hint = problem_hint,
            no_of_test_cases = no_of_test_cases
        )
    )

    try:
        db_session_ac.add(new_problem_statement_master)
        db_session_ac.commit()
        return jsonify({'message': 'problem stored successfully'}), 200
    except Exception as e:
        db_session_ac.rollback()
        return jsonify({'error': e}), 500


@app.route('/edit-problem', methods=['PUT'])
@jwt_required()
def edit_problem():
    data = request.json
    problem_to_be_edited = data['problem_to_be_edited']
    requester_id = data['requester_user_id']
    edit_metadata = data['edit_metadata']

    requesterUser = db_session_ac.query(UserMaster).filter_by(user_uuid=requester_id).first()

    if(requesterUser.user_metadata.is_admin):
        requestedProblem = db_session_ac.query(ProblemStatementMaster).filter_by(problem_statement_uuid=problem_to_be_edited).first()
        try:
            for field, model_attr in problem_update_fields.items():
                if field in edit_metadata and edit_metadata.get(field) is not None:
                    setattr(requestedProblem.problem_statement_metadata, model_attr.split('.')[-1], edit_metadata[field])
            db_session_ac.commit()
            return jsonify({'message': 'problem details edited successfully'}), 200
        except Exception as e:
            return jsonify({'error': 'problem details cannot be edited'}), 400
    else:
        return jsonify({'error' : 'You donot have the permission to perform the action'}), 403



@app.route('/delete-problem', methods=['DELETE'])
@jwt_required()
def delete_problem():
    data = request.json
    requested_problem_id = data['requested_problem_id']
    requester_user_id = data['requester_user_id']

    requesterUser = db_session_ac.query(UserMaster).filter_by(user_uuid=requester_user_id).first()
    if(requesterUser.user_metadata.is_admin):
        requestedProblem = db_session_ac.query(ProblemStatementMaster).filter_by(problem_statement_uuid=requested_problem_id).first()
        try:
            db_session_ac.delete(requestedProblem)
            db_session_ac.commit()
            return jsonify({'message' : 'problem deleted successfully'}), 200
        except Exception as e:
            return jsonify({'message' : 'error deleting problem'}), 400
    else:
        return jsonify({'error' : 'You donot have the permission to perform the action'}), 403


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
