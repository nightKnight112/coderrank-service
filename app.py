from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import subprocess
import docker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from database_utils.models import LanguageInfo, UserMetadata, UserMaster, ProblemStatementMaster, ProblemStatementMetadata, ProblemStatementTestCases, BlacklistedTokens
import uuid
from database_utils.dbUtils import user_update_fields, problem_update_fields, problem_testcases_update_fields
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import timedelta, datetime
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
# print(utils.generate_random_secret_key(32))
# jwt_secret_key = os.popen("openssl rand -hex 32").read()
jwt_secret_key = utils.generate_random_secret_key(32)
app.config["JWT_SECRET_KEY"] = jwt_secret_key
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=5)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(minutes=30)
app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]
app.config['JWT_COOKIE_CSRF_PROTECT'] = False

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

@app.route('/add-language-options', methods=['POST'])
def add_language_options():
    data = request.json
    user_id = data['user_id']
    language_options = data['language_options']

    isUserAdmin = db_session_ac.query(UserMaster).filter_by(user_uuid=user_id).first().user_metadata.is_admin

    if(isUserAdmin):

        errorFlag = False

        for ele in language_options:
            temp_uuid = uuid.uuid4()
            langObj = LanguageInfo(
                language_uuid=temp_uuid,
                language_name=ele.language_name
            )
            try:
                db_session_ac.add(langObj)
                db_session_ac.commit()
            except Exception as e:
                errorFlag = True
                print(e)
                break
        
        if(errorFlag):
            return jsonify({'message' : 'failed to add languages'}), 400
        else:
            return jsonify({'message' : 'added language info successfully'}), 200
    else:
        return jsonify({'message' : 'privillege escalation attempted'}), 403



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
                response.set_cookie("refresh_token_cookie", refresh_token, httponly=True, secure=True, samesite="None", max_age=timedelta(minutes=30))
            else:
                response.set_cookie("refresh_token_cookie", refresh_token, httponly=True, max_age=timedelta(minutes=30))
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
    try:
        identity = get_jwt_identity()
        refresh_token = request.cookies["refresh_token_cookie"]
        if db_session_ac.query(BlacklistedTokens).filter_by(blacklisted_token=str(hash(refresh_token))).count() != 0:
            return jsonify({"message": "Token expired or invalid"}), 401

        user_uuid = utils.decode_token(refresh_token, jwt_secret_key)["user_uuid"]
        print(user_uuid)
        new_access_token =  create_access_token(identity, additional_claims={"user_uuid": user_uuid})

        return jsonify({"access_token": new_access_token})
    
    except Exception as e:
        logging.error(e)
        return jsonify({"message": "Something went wrong"}), 500

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

@app.route("/logout", methods=["POST"])
@jwt_required(refresh=True)
def logout():
    try:
        refresh_token = request.cookies["refresh_token_cookie"]
        bt = BlacklistedTokens(blacklisted_token=hash(refresh_token), blacklisted_timestamp=datetime.now())
        db_session_ac.add(bt)
        db_session_ac.commit()
        response = make_response(jsonify({"message": "Logout successful"}))
        if environment == "local": 
            response.set_cookie("refresh_token_cookie", refresh_token, httponly=True, secure=True, samesite="None", max_age=timedelta(minutes=0))
        else:
            response.set_cookie("refresh_token_cookie", refresh_token, httponly=True, max_age=timedelta(minutes=0))
        
        blacklisted_tokens = db_session_ac.query(BlacklistedTokens).all()
        
        for i, value in enumerate(blacklisted_tokens):
            current_time = datetime.now()
            time_difference = current_time - value.blacklisted_timestamp
            if (time_difference.seconds / 60) > 30:
                db_session_ac.delete(value)        
        
        db_session_ac.commit()
        return response
    except Exception as e:
        logging.error(e)
        return jsonify({"message": "Something went wrong"}), 500

@app.route("/get-user-data", methods=['GET'])
@jwt_required()
def get_user_data():
    response = {}
    try:
        token = request.headers['Authorization'].split()[1]
        user_alias = utils.decode_token(token, secret=jwt_secret_key)["sub"]

        user_data = db_session_ac.query(UserMetadata).filter_by(user_alias=user_alias).first()
        response = {
            "message": "User details fetched successfully",
            "user_id": user_data.user_id,
            "user_name": user_data.user_name,
            "user_phone_no": user_data.user_phone_no,
            "user_email": user_data.user_email,
            "no_of_times_user_login": user_data.no_of_times_user_login,
            "no_of_problems_solved": user_data.no_of_problems_solved,
            "is_admin": user_data.is_admin
        }

        return jsonify(response)
    except Exception as e:
        logging.error(e)
        response = {
            "message": "Something went wrong"
        }
        return jsonify(response), 500

@app.route('/user-details-list/', defaults={'user_uuid': None}, methods=['GET'])
@app.route('/user-details-list/<string:user_uuid>', methods=['GET'])
@jwt_required()
def get_user_details_list(user_uuid):
    if user_uuid is None:
        userDetails = db_session_ac.query(UserMaster).options(joinedload(UserMaster.user_metadata)).all()
        resBody = []
        for users in userDetails:
            temp = {
                'user_id' : users.user_uuid,
                "full_name" : users.user_metadata.user_name,
                "user_alias" : users.user_metadata.user_alias,
                "phone_no" : users.user_metadata.user_phone_no,
                "email" : users.user_metadata.user_email,
                "user_login_count" : users.user_metadata.no_of_times_user_login,
                "problem_solved_count" : users.user_metadata.no_of_problems_solved,
                "is_admin": str(users.user_metadata.is_admin)
                
            }
            resBody.append(temp)

        # print(resBody)
        return jsonify(resBody), 200
    else:
        try:
            userDetails = db_session_ac.query(UserMaster).options(joinedload(UserMaster.user_metadata)).filter_by(user_uuid=user_uuid).first()
            temp = {
                        'user_id' : userDetails.user_uuid,
                        "full_name" : userDetails.user_metadata.user_name,
                        "user_alias" : userDetails.user_metadata.user_alias,
                        "phone_no" : userDetails.user_metadata.user_phone_no,
                        "email" : userDetails.user_metadata.user_email,
                        "user_login_count" : userDetails.user_metadata.no_of_times_user_login,
                        "problem_solved_count" : userDetails.user_metadata.no_of_problems_solved,
                        "is_admin": str(userDetails.user_metadata.is_admin)
                        
                    }
            return jsonify(temp), 200
        except Exception as e:
            logging.error(e)
            return jsonify({"message": "User not found"}), 404

@app.route('/delete-user', methods=['DELETE'])
@jwt_required()
def delete_user():
    data = request.json
    user_to_be_deleted = data['user_to_be_deleted']
    requester_id = utils.decode_token(request.headers["Authorization"].split()[1], jwt_secret_key)["user_uuid"]

    requestedUser = db_session_ac.query(UserMaster).filter_by(user_uuid=user_to_be_deleted).first()

    if(requestedUser):

        if(requester_id == user_to_be_deleted): #user self-delete logic
            try:
                db_session_ac.delete(requestedUser)
                db_session_ac.commit()
                response = make_response(jsonify({'message': 'User deleted successfully', 'self_delete': 'true'}))
                
                refresh_token = request.cookies["refresh_token_cookie"]
                bt = BlacklistedTokens(blacklisted_token=hash(refresh_token), blacklisted_timestamp=datetime.now())
                db_session_ac.add(bt)
                db_session_ac.commit()
                
                if environment == "local": 
                    response.set_cookie("refresh_token_cookie", refresh_token, httponly=True, secure=True, samesite="None", max_age=timedelta(minutes=0))
                else:
                    response.set_cookie("refresh_token_cookie", refresh_token, httponly=True, max_age=timedelta(minutes=0))
                    
                return response
            except Exception as e:
                logging.error(e)
                return jsonify({'message': 'Cannot delete user, user does not exist'}), 404
        
        else: #admin deletes user logic
            requesterUser = db_session_ac.query(UserMaster).filter_by(user_uuid=requester_id).first()
            if(requesterUser and requesterUser.user_metadata.is_admin):
                db_session_ac.delete(requestedUser)
                db_session_ac.commit()
                return jsonify({'message': 'User deleted successfully', 'self_delete': 'false'}), 200
            else:
                return jsonify({'message': 'Cannot delete user, user unauthorized or does not exist'}), 403
    
    else:
        return jsonify({"message": "User not found"}), 404

@app.route('/edit-user', methods=['PUT'])
@jwt_required()
def edit_user():
    data = request.json
    user_to_be_edited = data['user_to_be_edited']
    requester_id = utils.decode_token(request.headers["Authorization"].split()[1], secret=jwt_secret_key)["user_uuid"]
    edit_metadata = data['edit_metadata']

    requestedUser = db_session_ac.query(UserMaster).filter_by(user_uuid=user_to_be_edited).first()
    requesterUser = db_session_ac.query(UserMaster).filter_by(user_uuid=requester_id).first()

    if requestedUser:

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
                    return jsonify({'message': 'User details edited successfully'}), 200
                else:
                    return jsonify({'message': 'Privillege escalation attempted'}), 403
            except Exception as e:
                logging.error(e)
                return jsonify({'message': 'User details cannot be edited'}), 400
        else:
            if(requesterUser and requesterUser.user_metadata.is_admin):
                for field, model_attr in user_update_fields.items():
                    if field in edit_metadata and edit_metadata.get(field) is not None:
                        setattr(requestedUser.user_metadata, model_attr.split('.')[-1], edit_metadata[field])
                db_session_ac.commit()
                return jsonify({'message': 'User details edited successfully'}), 200
            else:
                return jsonify({'message': 'Cannot modify user'}), 400
    
    else:
        return jsonify({'message': 'User not found'}), 404


# problem end APIs

@app.route("/get-problem-details/<string:problem_id>", methods=["GET"])
@jwt_required()
def get_problem_details(problem_id):
    try:
        user_uuid = utils.decode_token(request.headers["Authorization"].split()[1], jwt_secret_key)["user_uuid"]
        user_obj = db_session_ac.query(UserMaster).filter_by(user_uuid=user_uuid).first()

        if user_obj.user_metadata.is_admin:
            problem_statement_obj = db_session_ac.query(ProblemStatementMaster).filter_by(problem_statement_uuid=problem_id).first()
            response = {
                "problem_statement_uuid" : problem_statement_obj.problem_statement_uuid,
                "problem_statement_title" : problem_statement_obj.problem_statement_metadata.problem_statement_title,
                "problem_statement_body" : problem_statement_obj.problem_statement_metadata.problem_statement_body,
                "problem_statement_duration" : problem_statement_obj.problem_statement_metadata.problem_statement_duration,
                "problem_statement_tags": problem_statement_obj.problem_statement_metadata.problem_statement_tags,
                "problem_statement_difficulty": problem_statement_obj.problem_statement_metadata.problem_statement_difficulty
            }

            test_cases = db_session_ac.query(ProblemStatementTestCases).filter_by(problem_statement_id=problem_statement_obj.problem_statement_id).all()

            temp_list = []
            for i in test_cases:
                temp = {
                    "test_case_id": i.test_case_id,
                    "input": i.input,
                    "expected_output": i.expected_output,
                    "test_case_weightage": i.test_case_weightage,
                    "is_hidden": i.is_hidden,
                }
                temp_list.append(temp)

            response["test_cases"] = temp_list

            return jsonify(response)
        else:
            return jsonify({"message": "You are unauthorized to perform this action"}), 403
    except Exception as e:
        logging.error(e)
        return jsonify({"message": "Something went wrong"}), 500

@app.route('/get-problem-list/', defaults={"problem_id": None}, methods=['GET'])
@app.route('/get-problem-list/<string:problem_id>',  methods=['GET'])
def get_problem_list(problem_id):
    try:
        # to fetch details of a problem
        if(problem_id):
            response = {}
            problem_statement_obj = db_session_ac.query(ProblemStatementMaster).filter_by(problem_statement_uuid=problem_id).first()
            response = {
                "problem_statement_uuid" : problem_statement_obj.problem_statement_uuid,
                "problem_statement_title" : problem_statement_obj.problem_statement_metadata.problem_statement_title,
                "problem_statement_body" : problem_statement_obj.problem_statement_metadata.problem_statement_body,
                "problem_statement_duration" : problem_statement_obj.problem_statement_metadata.problem_statement_duration,
                "problem_statement_tags": problem_statement_obj.problem_statement_metadata.problem_statement_tags,
                "problem_statement_difficulty": problem_statement_obj.problem_statement_metadata.problem_statement_difficulty
            }
        
            return jsonify(response)

        # to fetch problem list
        else:
            allProblemList = []
            allProblemObject = db_session_ac.query(ProblemStatementMaster).all()

            for problems in allProblemObject:
                temp = {
                    "problem_statement_uuid" : problems.problem_statement_uuid,
                    "problem_statement_title" : problems.problem_statement_metadata.problem_statement_title,
                    "problem_statement_body" : problems.problem_statement_metadata.problem_statement_body,
                    "problem_statement_duration" : problems.problem_statement_metadata.problem_statement_duration,
                    "problem_statement_tags": problems.problem_statement_metadata.problem_statement_tags,
                    "problem_statement_difficulty": problems.problem_statement_metadata.problem_statement_difficulty
                }

                allProblemList.append(temp)
            
            return jsonify(allProblemList)
    
    except Exception as e:
        logging.error(e)
        return jsonify({"message": "Something went wrong"}), 500

@app.route('/add-problem', methods=['POST'])
@jwt_required()
def add_problem():
    data = request.json
    problem_statement_uuid = uuid.uuid4()
    problem_statement_title = data['problem_statement_title']
    problem_statement_body = data['problem_statement_body']
    problem_statement_duration = data['problem_statement_duration']
    problem_statement_difficulty = data['problem_statement_difficulty']
    problem_statement_tags = data['problem_statement_tags']
    test_case_data = data['test_cases']

    new_problem_statement_master = ProblemStatementMaster(
        problem_statement_uuid = problem_statement_uuid,
        problem_statement_metadata = ProblemStatementMetadata(
            problem_statement_title = problem_statement_title,
            problem_statement_body= problem_statement_body,
            problem_statement_duration = problem_statement_duration,
            problem_statement_difficulty = problem_statement_difficulty,
            problem_statement_tags = problem_statement_tags
        )
    )

    try:
        db_session_ac.add(new_problem_statement_master)
        db_session_ac.commit()

        if(test_case_data):
            errorFlag = False

            problem_statement_id = new_problem_statement_master.problem_statement_id

            for ele in test_case_data:
                tempObj = ProblemStatementTestCases(
                    problem_statement_id=problem_statement_id,
                    input=ele["input"],
                    expected_output=ele["expected_output"],
                    test_case_weightage=ele["test_case_weightage"],
                    is_hidden=ele["is_hidden"]
                )
                try:
                    db_session_ac.add(tempObj)
                    db_session_ac.commit()
                except Exception as e: 
                    logging.error(e)
                    db_session_ac.rollback()
                    errorFlag = True
            
            if(errorFlag):
                return jsonify({ 'message' : 'Something went wrong' }), 500
            else:
                return jsonify({'message' : 'Problem statement added successfully'})
        
        else:
            return jsonify({'message': 'Problem statement added successfully'})
    
    except Exception as e:
        logging.error(e)
        db_session_ac.rollback()
        return jsonify({'message': "Something went wrong"}), 500


@app.route('/edit-problem', methods=['PUT'])
@jwt_required()
def edit_problem():
    data = request.json
    problem_to_be_edited = data['problem_to_be_edited']
    requester_id = utils.decode_token(request.headers["Authorization"].split()[1], jwt_secret_key)["user_uuid"]
    edit_metadata = data['edit_metadata']

    requesterUser = db_session_ac.query(UserMaster).filter_by(user_uuid=requester_id).first()

    if(requesterUser and requesterUser.user_metadata.is_admin):
        requested_problem = db_session_ac.query(ProblemStatementMaster).filter_by(problem_statement_uuid=problem_to_be_edited).first()

        try:
            requested_problem.problem_statement_metadata.problem_statement_title = edit_metadata["problem_statement_title"]
            requested_problem.problem_statement_metadata.problem_statement_body = edit_metadata["problem_statement_body"]
            requested_problem.problem_statement_metadata.problem_statement_duration = edit_metadata["problem_statement_duration"]
            requested_problem.problem_statement_metadata.problem_statement_difficulty = edit_metadata["problem_statement_difficulty"]
            requested_problem.problem_statement_metadata.problem_statement_tags = edit_metadata["problem_statement_tags"]


            requested_problem_test_cases = db_session_ac.query(ProblemStatementTestCases).filter_by(problem_statement_id=requested_problem.problem_statement_id).all()

            for i in edit_metadata["test_cases"]:
                # for new test cases
                if i["test_case_id"] == "":
                    new_test_case = ProblemStatementTestCases(problem_statement_id=requested_problem.problem_statement_id,
                                                              input=i["input"],
                                                              expected_output=i["expected_output"],
                                                              test_case_weightage=i["test_case_weightage"],
                                                              is_hidden=i["is_hidden"])
                    
                    db_session_ac.add(new_test_case)
                
                # for existing test cases
                else:
                    for j in requested_problem_test_cases:
                        if i["test_case_id"] == j.test_case_id:
                            j.input = i["input"]
                            j.expected_output = i["expected_output"]
                            j.test_case_weightage = i["test_case_weightage"]
                            j.is_hidden = i["is_hidden"]

                            break

            db_session_ac.commit()
            return jsonify({"message": "Problem statement updated successfully"})
            
                    
        except Exception as e:
            logging.error(e)
            db_session_ac.rollback()
            return jsonify({'message': 'Something went wrong'}), 500
        
    else:
        return jsonify({'message' : 'You are unauthorized to perform the action'}), 403



@app.route('/delete-problem', methods=['DELETE'])
@jwt_required()
def delete_problem():
    data = request.json
    requested_problem_id = data['requested_problem_id']
    requester_user_id = utils.decode_token(request.headers["Authorization"].split()[1], jwt_secret_key)["user_uuid"]

    requesterUser = db_session_ac.query(UserMaster).filter_by(user_uuid=requester_user_id).first()
    if(requesterUser and requesterUser.user_metadata.is_admin):
        requestedProblem = db_session_ac.query(ProblemStatementMaster).filter_by(problem_statement_uuid=requested_problem_id).first()
        try:
            db_session_ac.delete(requestedProblem)
            db_session_ac.commit()
            return jsonify({'message' : 'Problem statement deleted successfully'})
        except Exception as e:
            return jsonify({'message' : 'Something went wrong'}), 500
    else:
        return jsonify({'message' : 'You are unauthorized to perform the action'}), 403

#get all test cases for problems
# @app.route('/get-test-cases/<string:requested_problem_uuid>', methods=['GET'])
# def get_test_cases(requested_problem_uuid):
#     problem_data = db_session_ac.query(ProblemStatementMaster).filter_by(problem_statement_uuid=requested_problem_uuid).first()
#     all_test_cases_obj_list = db_session_ac.query(ProblemStatementTestCases).filter_by(problem_statement_id=problem_data.problem_statement_id).all()
#     res_json = []
#     for ele in all_test_cases_obj_list:
#         temp = {
#             'test_case_id' : ele.test_case_id,
#             'expected_input' :  ele.expected_input,
#             'expected_output' : ele.expected_output,
#             'test_case_weightage' : ele.test_case_weightage,
#             'is_hidden' : ele.is_hidden
#         }
#         res_json.append(temp)
#     return jsonify(res_json), 200

# #create test cases for problems
# @app.route('/add-test-cases', methods=['POST'])
# @jwt_required()
# def add_test_cases():
#     '''
#         expected request payload
#         {
#             problem_id : problem_uuid,
#             test_cases : [
#                 {
#                     input : '',
#                     output : '',
#                     weightage : '',
#                     hidden : ''
#                 }, ...
#             ]
#         }
#     '''
#     data = request.json
#     errorFlag = False
#     problem_uuid = data['problem_id']
#     problem_statement_id = db_session_ac.query(ProblemStatementMaster).filter_by(problem_statement_uuid=problem_uuid).first().problem_statement_id
#     test_cases_array = data['test_cases']

#     for ele in test_cases_array:
#         tempObj = ProblemStatementTestCases(
#             problem_statement_id=problem_statement_id,
#             expected_input=ele.input,
#             expected_output=ele.output,
#             test_case_weightage=ele.weightage,
#             is_hidden=ele.hidden
#         )
#         try:
#             db_session_ac.add(tempObj)
#             db_session_ac.commit()
#         except Exception as e: 
#             db_session_ac.rollback()
#             errorFlag = True
#     if(errorFlag):
#         return jsonify({ 'message' : 'test cases not added successfully, please check with super admin for more info' }), 400
#     else:
#         return jsonify({'message' : 'added test cases for problem statement successfully'}), 200

#edit test cases for problems
# @app.route('/edit-test-cases', methods=['PUT'])
# @jwt_required()
# def edit_test_cases():
#     data = request.json
#     test_case_id = data['test_case_id']
#     requester_id = data['requester_id']
#     edit_metadata = data['edit_metadata']
#     user_obj = db_session_ac.query(UserMaster).filter_by(user_uuid=requester_id).first()
#     if(user_obj.user_metadata.is_admin):
#         test_case_obj = db_session_ac.query(ProblemStatementTestCases).filter_by(test_case_id=test_case_id).first()
#         for field, model_attr in problem_testcases_update_fields:
#             if field in edit_metadata and edit_metadata.get(field) is not None:
#                 setattr(test_case_obj, model_attr.split('.')[-1], edit_metadata[field])
#         try:
#             db_session_ac.add(test_case_obj)
#             db_session_ac.commit()
#             return jsonify({'message' : 'Test case details edited successfully'}),200
#         except Exception as e:
#             db_session_ac.rollback()
#             return jsonify({'message' : 'Problem editing test case details'}),400
#     else:
#         return jsonify({'message': 'privillege escalation attempted'}), 403

#delete test cases for problems
@app.route('/delete-test-case', methods=['DELETE'])
@jwt_required()
def delete_test_cases():
    data = request.json
    test_case_id = data['test_case_id']
    requester_id = utils.decode_token(request.headers["Authorization"].split()[1], jwt_secret_key)["user_uuid"]
    user_obj = db_session_ac.query(UserMaster).filter_by(user_uuid=requester_id).first()
    if(user_obj and user_obj.user_metadata.is_admin):
        test_case_obj = db_session_ac.query(ProblemStatementTestCases).filter_by(test_case_id=test_case_id).first()
        try:
            db_session_ac.delete(test_case_obj)
            db_session_ac.commit()
            return jsonify({'message' : 'Test case deleted successfully'}), 200
        except Exception as e:
            return jsonify({'message' : 'Something went wrong'}), 500
    else:
        return jsonify({'message': 'You are unauthorized to perform this action'}), 403


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
