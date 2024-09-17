CREATE TABLE "language_info" (
  "language_id" integer PRIMARY KEY NOT NULL,
  "language_uuid" varchar,
  "language_name" varchar
);

CREATE TABLE "problem_statement_master" (
  "problem_statement_id" integer PRIMARY KEY NOT NULL,
  "problem_statement_uuid" varchar
);

CREATE TABLE "problem_statement_metadata" (
  "problem_statement_id" integer PRIMARY KEY NOT NULL,
  "problem_statement_body" longtext,
  "sample_input" varchar,
  "sample_output" varchar,
  "problem_duration" integer,
  "problem_hint" text,
  "no_of_test_cases" integer
);

CREATE TABLE "problem_statement_test_cases" (
  "problem_statement_id" integer,
  "language_id" integer,
  "expected_input" varchar,
  "expected_output" varchar,
  "test_case_weightage" integer,
  "is_hidden" boolean
);

CREATE TABLE "user_master" (
  "user_id" integer PRIMARY KEY NOT NULL,
  "user_uuid" varchar
);

CREATE TABLE "user_metadata" (
  "user_id" integer PRIMARY KEY NOT NULL,
  "user_name" varchar,
  "user_alias" varchar,
  "user_password" varchar,
  "user_phone_no" varchar,
  "user_email" varchar,
  "no_of_times_user_login" integer,
  "no_of_problems_solved" integer,
  "is_admin" boolean
);

CREATE TABLE "user_did_problem" (
  "user_id" integer,
  "problem_statement_id" integer
);

ALTER TABLE "problem_statement_test_cases" ADD FOREIGN KEY ("language_id") REFERENCES "language_info" ("language_id");

ALTER TABLE "problem_statement_test_cases" ADD FOREIGN KEY ("problem_statement_id") REFERENCES "problem_statement_master" ("problem_statement_id");

ALTER TABLE "problem_statement_metadata" ADD FOREIGN KEY ("problem_statement_id") REFERENCES "problem_statement_master" ("problem_statement_id");

ALTER TABLE "user_metadata" ADD FOREIGN KEY ("user_id") REFERENCES "user_master" ("user_id");

ALTER TABLE "user_did_problem" ADD FOREIGN KEY ("user_id") REFERENCES "user_master" ("user_id");

ALTER TABLE "user_did_problem" ADD FOREIGN KEY ("problem_statement_id") REFERENCES "problem_statement_master" ("problem_statement_id");
