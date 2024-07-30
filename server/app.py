from flask import request, make_response, send_from_directory, session
from flask_restful import Resource
import os

from server.config import app, db, api
from server.models import User, Project, Class, Cohort, Review, Destination
@app.route('/')
def index():
    return '<h1>Project_Tracker</h1>'

class Users(Resource):
    def get(self):
        users = User.query.all()
        return [user.to_dict() for user in users]
class UserByID(Resource):
    def get(self, user_id):
        user = User.query.filter_by(id=user_id).first()

        if user:
            return user.to_dict()
        else:
            return {'message': 'User not found'}, 404

    def delete(self, user_id):
        user = User.query.filter_by(id=user_id).first()

        if user:
            db.session.delete(user)
            db.session.commit()
            return {'message': 'User deleted'}
        else:
            return {'message': 'User not found'}, 404
        
    def patch(self, user_id):
        user = User.query.filter_by(id=user_id).first()

        if user:
            if 'username' in request.json:
                user.username = request.json['username']
            if 'email' in request.json:
                user.email = request.json['email']
            if 'password' in request.json:
                user.password = request.json['password']
            db.session.commit()
            return user.to_dict()
        else:
            return {'message': 'User not found'}, 404
        
class UserByUsername(Resource):
    def get(self, username):
        user = User.query.filter_by(username=username).first()

        if user:
            return user.to_dict()
        else:
            return {'message': 'User not found'}, 404
        
    def delete(self, username):
        user = User.query.filter_by(username=username).first()

        if user:
            db.session.delete(user)
            db.session.commit()
            return {'message': 'User deleted'}
        else:
            return {'message': 'User not found'}, 404

    def patch(self, username):
        user = User.query.filter_by(username=username).first()

        if user:
            if 'username' in request.json:
                user.username = request.json['username']
            if 'email' in request.json:
                user.email = request.json['email']
            if 'password' in request.json:
                user.password = request.json['password']
            db.session.commit()
            return user.to_dict()
        else:
            return {'message': 'User not found'}, 404
        
class Projects(Resource):
    def get(self):
        projects = [project.to_dict() for project in Project.query.all()]
        return make_response(projects, 200)

    def post(self):
        try:
            project = Project(name=request.form.get('name'),
                              description=request.form.get('description'),
                              github_link=request.form.get('github_link'),
                              deployed_link=request.form.get('deployed_link'),
                              owner_id=session['user_id'])
            db.session.add(project)
            db.session.commit()
            return make_response(project.to_dict(), 201)
        except Exception as e:
            return make_response(str(e), 400)
class ProjectByID(Resource):
    def get(self, project_id):
        project = Project.query.filter_by(id=project_id).first()

        if project:
            return make_response(project.to_dict(), 200)
        else:
            return make_response({'message': 'Project not found'}, 404)
    def delete(self, project_id):
        project = Project.query.filter_by(id=project_id).first() 
        if project:
            db.session.delete(project)
            db.session.commit()
            return make_response({'message': 'Project deleted'}, 200)
        else:
            return make_response({'message': 'Project not found'}, 404)
    
    def patch(self, project_id):
        project = Project.query.filter_by(id=project_id).first()
        if project:
            if 'name' in request.json:
                project.name = request.json['name']
            if 'description' in request.json:
                project.description = request.json['description']
            if 'github_link' in request.json:
                project.github_link = request.json['github_link']
            if 'deployed_link' in request.json:
                project.deployed_link = request.json['deployed_link']
            db.session.commit()
            return make_response(project.to_dict(), 200)
        else:
            return make_response({'message': 'Project not found'}, 404)
      