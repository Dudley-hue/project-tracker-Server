from faker import Faker
from app import app,db
from models import User,Role,Project,Cohort,ProjectCohort,ProjectMember
import random

#generating a faker instance for generating fake data
faker=Faker()

def create_roles():
    roles=['admin','student']#list of roles to be created
    for role_name in roles:
        role=Role(name=role_name)
        db.session.add(role)
        db.session.commit()
        
def get_role_by_name(role_name):
    # query the role table so as to find a role by its name
    return Role.querry.filter_by(name=role_name).first()

def create_users(num_users):
    users=[]
    student_role=get_role_by_name('student')
    for _ in range(num_users):
        users=
        