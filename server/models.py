from app import db
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates
import re
from werkzeug.security import generate_password_hash, check_password_hash
#testing
class User(db.Model):
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    role_id = Column(Integer, ForeignKey('role.id'), nullable=False)
    role = relationship('Role', back_populates='users')
    projects = relationship('Project', back_populates='owner')
    project_memberships = relationship('ProjectMember', back_populates='user')
    
    @validates('username')
    def validate_username(self, key, username):
        user = User.query.filter_by(username=username).first()
        if user:
            raise AssertionError('Username already exists')
        return username
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    @validates('password_hash')
    def validate_password(self, key, password):
        if len(password) < 8:
            raise AssertionError('Password must be at least 8 characters long')
        return password
    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError('Invalid email address')
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            raise ValueError('Email already exists')
        return email

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    owner = relationship('User', back_populates='projects')
    project_members = relationship('ProjectMember', back_populates='project')
    project_cohorts = relationship('ProjectCohort', back_populates='project')
    classroom_id = Column(Integer, ForeignKey('cohort.id'), nullable=False)
    classroom = relationship('Classroom', back_populates='projects')
    @validates('name')
    def validate_name(self, key, name):
        if len(name) < 7:
            raise AssertionError('Project name must be at least 7 characters long')
        return name
     
    @validates('github_link')
    def validate_github_link(self, key, github_link):
        if not github_link.startswith('https://github.com/'):
            raise AssertionError('GitHub link must start with "https://github.com/"')
        return github_link
    
    @validates('description')
    def validate_description(self, key, description):
        if len(description) < 20:
            raise AssertionError('Project description must be at least 20 characters long')
        return description
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'owner_id': self.owner_id,
            'github_link': self.github_link
        }

class Cohort(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(200))
    project_cohorts = relationship('ProjectCohort', back_populates='cohort')
    classrooms = relationship('Classroom', back_populates='cohort')
class ProjectMember(db.Model):
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    project = relationship('Project', back_populates='project_members')
    user = relationship('User', back_populates='project_memberships')

class ProjectCohort(db.Model):
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False)
    cohort_id = Column(Integer, ForeignKey('cohort.id'), nullable=False)
    project = relationship('Project', back_populates='project_cohorts')
    cohort = relationship('Cohort', back_populates='project_cohorts')
class Classroom(db.Model):
    id  = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(200))
    cohort_id = Column(Integer, ForeignKey('cohort.id'), nullable=False)
    cohort = relationship('Cohort', back_populates='classrooms')
    projects = relationship('Project', back_populates='classroom')
@validates('name')
def validate_name(self, key, name):
    if len(name) < 7:
      raise AssertionError('Classroom name must be at least 7 characters long')
    return name
@validates('description')
def validate_description(self, key, description):
    if len(description) < 20:
      raise AssertionError('Classroom description must be at least 20 characters long')
    return description