user_update_fields = {
    "full_name" : "user_metadata.user_name",
    "user_alias" : "user_metadata.user_alias",
    "user_password" : "user_metadata.user_password",
    "phone_no" : "user_metadata.user_phone_no",
    "email" : "user_metadata.user_email",
    "no_of_times_user_login" : "user_metadata.no_of_times_user_login",
    "no_of_problems_solved" : "user_metadata.no_of_problems_solved" ,
    "is_admin" : "user_metadata.is_admin"
}

problem_update_fields = {
    "statement_body": "problem_statement_metadata.problem_statement_body",
    "sample_input": "problem_statement_metadata.sample_input",
    "sample_output": "problem_statement_metadata.sample_output",
    "duration": "problem_statement_metadata.problem_duration",
    "no_of_test_cases": "problem_statement_metadata.no_of_test_cases"
}

problem_testcases_update_fields = {
    "expected_input": "problem_statement_test_cases.expected_input",
    "expected_output": "problem_statement_test_cases.expected_output",
    "test_case_weightage": "problem_statement_test_cases.test_case_weightage",
    "is_hidden": "problem_statement_test_cases.is_hidden",
}