from app import db
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship


# Define the models
class User(db.Model):
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    role_id = Column(Integer, ForeignKey('role.id'), nullable=False)
    role = relationship('Role', back_populates='users')

class Role(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    users = relationship('User', back_populates='role')

class Project(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    description = Column(String(500))
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    github_link = Column(String(200))
    
class Cohort(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(200))

class ProjectMember(db.Model):
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

class ProjectCohort(db.Model):
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False)
    cohort_id = Column(Integer, ForeignKey('cohort.id'), nullable=False)

