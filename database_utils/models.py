from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

Base = declarative_base()

class UserMetadata(Base):
    __tablename__ = "user_metadata"

    user_id = Column(Integer,ForeignKey('user_master.user_id'), primary_key=True)
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

    user_id = Column(Integer, primary_key=True)
    user_uuid = Column(String)

    user_metadata = relationship("UserMetadata", back_populates="user_master", uselist=False, cascade="all, delete")

class UserDidProblem(Base):
    __tablename__ = "user_did_problem"

    user_id = Column(Integer, primary_key=True)
    problem_statement_id = Column(Integer)

class LanguageInfo(Base):
    __tablename__ = "language_info"

    language_id = Column(Integer, primary_key=True)
    language_uuid = Column(String)
    language_name = Column(String)

class ProblemStatementTestCases(Base):

    __tablename__ = "problem_statement_test_cases"

    problem_statement_id = Column(Integer, primary_key=True)
    language_id = Column(Integer)
    expected_input = Column(String)
    expected_output = Column(String)
    test_case_weightage = Column(Integer)
    is_hidden = Column(Boolean)

class ProblemStatementMaster(Base):

    __tablename__ = "problem_statement_master"

    problem_statement_id = Column(Integer, primary_key=True)
    problem_statement_uuid = Column(String)
    problem_statement_metadata = relationship("ProblemStatementMetadata", back_populates="problem_statement_master", uselist=False, cascade="all, delete")

class ProblemStatementMetadata(Base):

    __tablename__ = "problem_statement_metadata"

    problem_statement_id = Column(Integer, ForeignKey('problem_statement_master.problem_statement_id'), primary_key=True)
    problem_statement_body = Column(Text)
    sample_input = Column(String)
    sample_output = Column(String)
    problem_duration = Column(Integer)
    problem_hint = Column(Text)
    no_of_test_cases = Column(Integer)

    problem_statement_master = relationship("ProblemStatementMaster", back_populates="problem_statement_metadata")