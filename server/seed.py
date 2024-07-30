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
        
        