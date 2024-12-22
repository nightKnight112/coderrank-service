from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class UserMetadata(Base):
    __tablename__ = "user_metadata"

    user_id = Column(Integer,ForeignKey('user_master.user_id'), primary_key=True, autoincrement=True)
    user_name = Column(String)
    user_alias = Column(String)
    user_password = Column(String)
    user_phone_no = Column(String)
    user_email = Column(String)
    no_of_times_user_login = Column(Integer)
    no_of_problems_solved = Column(Integer)
    is_admin = Column(Boolean)

    user_master = relationship("UserMaster", back_populates="user_metadata")

class UserMaster(Base):
    __tablename__ = "user_master"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    user_uuid = Column(String)

    user_metadata = relationship("UserMetadata", back_populates="user_master", uselist=False, cascade="all, delete")

class LanguageInfo(Base):
    __tablename__ = "language_info"

    language_id = Column(Integer, primary_key=True, autoincrement=True)
    language_name = Column(String)

    user_did_problem = relationship("UserDidProblem", back_populates="language_info", uselist=False, cascade="all, delete")

class UserDidProblem(Base):
    __tablename__ = "user_did_problem"

    user_id = Column(Integer, primary_key=True)
    problem_statement_id = Column(Integer, primary_key=True)
    language_id = Column(Integer, ForeignKey('language_info.language_id'), primary_key=True)
    code = Column(String, nullable=False)
    test_cases_passed = Column(Integer, nullable=False)
    total_test_cases = Column(Integer, nullable=False)

    language_info = relationship("LanguageInfo", back_populates="user_did_problem")

class ProblemStatementTestCases(Base):

    __tablename__ = "problem_statement_test_cases"
    test_case_id = Column(Integer, primary_key=True, autoincrement=True)
    problem_statement_id = Column(Integer, ForeignKey('problem_statement_master.problem_statement_id'))
    input = Column(String)
    expected_output = Column(String)
    test_case_weightage = Column(Integer)
    is_hidden = Column(Boolean)

    problem_statement_master = relationship("ProblemStatementMaster", back_populates="problem_statement_test_cases")

class ProblemStatementMaster(Base):

    __tablename__ = "problem_statement_master"

    problem_statement_id = Column(Integer, primary_key=True, autoincrement=True)
    problem_statement_uuid = Column(String)
    
    problem_statement_metadata = relationship("ProblemStatementMetadata", back_populates="problem_statement_master", uselist=False, cascade="all, delete")

    problem_statement_test_cases = relationship("ProblemStatementTestCases", back_populates="problem_statement_master", cascade="all, delete")

class ProblemStatementMetadata(Base):

    __tablename__ = "problem_statement_metadata"

    problem_statement_id = Column(Integer, ForeignKey('problem_statement_master.problem_statement_id'), primary_key=True, autoincrement=True)
    problem_statement_title = Column(String)
    problem_statement_body = Column(Text)
    problem_statement_duration = Column(Integer)
    problem_statement_difficulty = Column(String)
    problem_statement_tags = Column(Text)

    problem_statement_master = relationship("ProblemStatementMaster", back_populates="problem_statement_metadata")

class BlacklistedTokens(Base):
    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    blacklisted_token = Column(String)
    blacklisted_timestamp = Column(DateTime)
