CREATE DATABASE coderrank_db
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'English_India.1252'
    LC_CTYPE = 'English_India.1252'
    LOCALE_PROVIDER = 'libc'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

COMMENT ON DATABASE coderrank_db
    IS 'Coderrank DB';

DROP TABLE IF EXISTS language_info CASCADE;
DROP TABLE IF EXISTS problem_statement_master CASCADE;
DROP TABLE IF EXISTS problem_statement_metadata CASCADE;
DROP TABLE IF EXISTS problem_statement_test_cases CASCADE;
DROP TABLE IF EXISTS user_master CASCADE;
DROP TABLE IF EXISTS user_metadata CASCADE;
DROP TABLE IF EXISTS user_did_problem CASCADE;
DROP TABLE IF EXISTS test_cases_in_language CASCADE;

-- Table: language_info
CREATE TABLE language_info (
  language_id BIGSERIAL PRIMARY KEY NOT NULL,
  language_uuid VARCHAR,
  language_name VARCHAR
);

-- Table: problem_statement_master
CREATE TABLE problem_statement_master (
  problem_statement_id BIGSERIAL PRIMARY KEY NOT NULL,
  problem_statement_uuid VARCHAR
);

-- Table: problem_statement_metadata
CREATE TABLE problem_statement_metadata (
  problem_statement_id BIGSERIAL PRIMARY KEY NOT NULL,
  problem_statement_title VARCHAR,
  problem_statement_body TEXT,
  problem_statement_duration INTEGER,
  problem_statement_difficulty VARCHAR(10),
  problem_statement_tags TEXT,
  CONSTRAINT fk_problem_statement_metadata
    FOREIGN KEY (problem_statement_id)
    REFERENCES problem_statement_master(problem_statement_id)
);

-- Table: problem_statement_test_cases
CREATE TABLE problem_statement_test_cases (
  test_case_id BIGSERIAL PRIMARY KEY NOT NULL,
  problem_statement_id INTEGER NOT NULL,
  input VARCHAR,
  expected_output VARCHAR,
  test_case_weightage INTEGER,
  is_hidden BOOLEAN,
  CONSTRAINT fk_problem_statement_test_cases_problem
    FOREIGN KEY (problem_statement_id)
    REFERENCES problem_statement_master(problem_statement_id)
);

-- Table: user_master
CREATE TABLE user_master (
  user_id BIGSERIAL PRIMARY KEY NOT NULL,
  user_uuid VARCHAR
);

-- Table: user_metadata
CREATE TABLE user_metadata (
  user_id BIGSERIAL PRIMARY KEY NOT NULL,
  user_name VARCHAR,
  user_alias VARCHAR,
  user_password VARCHAR,
  user_phone_no VARCHAR,
  user_email VARCHAR,
  no_of_times_user_login INTEGER,
  no_of_problems_solved INTEGER,
  is_admin BOOLEAN,
  CONSTRAINT fk_user_metadata
    FOREIGN KEY (user_id)
    REFERENCES user_master(user_id)
);

-- Table: user_did_problem
CREATE TABLE user_did_problem (
  user_id INTEGER NOT NULL,
  problem_statement_id INTEGER NOT NULL,
  code TEXT NOT NULL,
  test_cases_passed INTEGER NOT NULL,
  total_test_cases INTEGER NOT NULL,
  language_id INTEGER NOT NULL,
  PRIMARY KEY (user_id, problem_statement_id, language_id),
  CONSTRAINT fk_user_did_problem_user
    FOREIGN KEY (user_id)
    REFERENCES user_master(user_id),
  CONSTRAINT fk_user_did_problem_problem
    FOREIGN KEY (problem_statement_id)
    REFERENCES problem_statement_master(problem_statement_id),
  CONSTRAINT fk_user_did_problem_language_info
    FOREIGN KEY (language_id)
    REFERENCES language_info(language_id)
);

CREATE TABLE public.blacklisted_tokens (
	id bigserial NOT NULL,
	blacklisted_token varchar NULL,
	blacklisted_timestamp timestamp NULL,
	CONSTRAINT blacklisted_tokens_pkey PRIMARY KEY (id)
);