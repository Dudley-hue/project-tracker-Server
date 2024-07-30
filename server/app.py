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
      