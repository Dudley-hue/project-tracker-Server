from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func
import re 
from flask import url_for

from server.config import db, bcrypt


# Models go here!

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    
    serialize_rules = ['-reviews.user', '-destinations.destination']
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    _password = db.Column(db.String, nullable=False)
    
    reviews = db.relationship('Review', back_populates='user')
    destinations = association_proxy('reviews', 'destination')
    
    @validates('username')
    def validate_username(self, key, username):
        user = User.query.filter_by(username=username).first()
        if user:
            raise ValueError('Username already exists')
        return username
    
   
    @hybrid_property
    def password(self):
        return self._password
    
    @password.setter
    def password(self, password):
        if (
            len(password) < 8 or
            not re.search(r"[A-Z]", password) or
            not re.search(r"[a-z]", password) or
            not re.search(r"[0-9]", password) or
            not re.search(r"[\W_]", password)
        ):
            raise ValueError(
                'Password MUST be at least 8 digits, include uppercase, lowercase, numbers & special characters.'
            )

        password_hash = bcrypt.generate_password_hash(password.encode('utf-8'))
        self._password = password_hash.decode('utf-8')
    
    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password, password.encode('utf-8'))
    

    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError('Invalid email address')
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            raise ValueError('Email already exists')
        return email
    
class Class(db.Model):
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    cohort_id = db.Column(db.Integer, db.ForeignKey('cohorts.id'), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    project_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    github_link = db.Column(db.String(200), nullable=False)
    deployed_link = db.Column(db.String(200), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    cohorts = db.relationship('Cohort', secondary='project_cohorts', back_populates='projects')
    members = db.relationship('User', secondary='project_members', back_populates='projects_member')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'github_link': self.github_link,
            'deployed_link': self.deployed_link,
            'owner_id': self.owner_id,
            'cohorts': [cohort.id for cohort in self.cohorts],
            'members': [member.id for member in self.members]
        }
    
    class Cohort(db.Model):
        __tablename__ = 'cohorts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

    projects = db.relationship('Project', secondary='project_cohorts', back_populates='cohorts')

class ProjectMembers(db.Model):
    _tablename_ = 'project_members'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class ProjectCohorts(db.Model):
    _tablename_ = 'project_cohorts'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    cohort_id = db.Column(db.Integer, db.ForeignKey('cohorts.id'), nullable=False)


