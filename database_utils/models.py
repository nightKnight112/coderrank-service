from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean

Base = declarative_base()

class UserMetadata(Base):
    __tablename__ = "user_metadata"

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String)
    user_alias = Column(String)
    user_password = Column(String)
    user_phone_no = Column(String)
    user_email = Column(String)
    no_of_times_user_login = Column(Integer)
    no_of_problems_solved = Column(Integer)
    is_admin = Column(Boolean)

class UserMaster(Base):
    __tablename__ = "user_master"

    user_id = Column(Integer, primary_key=True)
    user_uuid = Column(String)

class UserDidProblem(Base):
    __tablename__ = "user_did_problem"

    user_id = Column(Integer, primary_key=True)
    problem_statement_id = Column(Integer)

class LanguageInfo(Base):
    __tablename__ = "language_info"

    language_id = Column(Integer, primary_key=True)
    language_uuid = Column(String)
    language_name = Column(String)