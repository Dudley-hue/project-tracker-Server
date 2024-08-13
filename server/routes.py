import jwt
import datetime
from functools import wraps
from flask import Blueprint, request, jsonify, current_app, session
from app import db
from models import User, Project, Cohort, Class, ProjectMember, Role
from werkzeug.security import generate_password_hash, check_password_hash

api_bp = Blueprint('api', __name__)

# Secret key for JWT encoding and decoding
SECRET_KEY = "your_secret_key_here"  # Replace with your actual secret key

# Decorator to check for valid JWT token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # Bearer token

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

# Test Route
@api_bp.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'API is working!'}), 200

# Register Route
@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role_id = data.get('role_id')  # role_id should be passed from the frontend

    if not username or not email or not password or not role_id:
        return jsonify({'error': 'Missing required fields'}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'User already exists'}), 400

    try:
        # Fetch the role based on role_id
        role = Role.query.get(role_id)
        
        if not role:
            return jsonify({'error': 'Role not found'}), 500

        # Create the new user
        new_user = User(username=username, email=email, role_id=role.id)
        new_user.set_password(password)  # Set the password using the method in the User model

        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to register user'}), 500

# Login Route
@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, SECRET_KEY, algorithm="HS256")

    return jsonify({'token': token, 'is_admin': user.role.name == 'admin'}), 200

# Check if Admin Route
@api_bp.route('/check_admin', methods=['GET'])
@token_required
def check_admin(current_user):
    if current_user.role.name == 'admin':
        return jsonify({'is_admin': True}), 200
    return jsonify({'is_admin': False}), 200

# Logout Route
@api_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    return jsonify({'message': 'Logout successful'}), 200

# Get All Projects
@api_bp.route('/projects', methods=['GET'])
@token_required
def get_projects(current_user):
    projects = Project.query.all()
    return jsonify([project.to_dict() for project in projects]), 200

# Get Single Project
@api_bp.route('/projects/<int:project_id>', methods=['GET'])
@token_required
def get_project(current_user, project_id):
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict()), 200

# Create New Project
@api_bp.route('/projects', methods=['POST'])
@token_required
def create_project(current_user):
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    github_link = data.get('github_link')
    owner_id = data.get('owner_id')
    class_id = data.get('class_id')
    poster_url = data.get('poster_url', '')  # Handle optional poster_url with default empty string

    if not name or not description or not owner_id or not class_id:
        return jsonify({'error': 'Missing required fields'}), 400

    new_project = Project(
        name=name,
        description=description,
        owner_id=owner_id,
        github_link=github_link,
        class_id=class_id,
        poster_url=poster_url
    )

    try:
        db.session.add(new_project)
        db.session.commit()
        return jsonify(new_project.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({'error': 'Failed to create project'}), 500

# Update a Project
@api_bp.route('/projects/<int:project_id>', methods=['PUT'])
@token_required
def update_project(current_user, project_id):
    project = Project.query.get_or_404(project_id)

    data = request.get_json()
    project.name = data.get('name', project.name)
    project.description = data.get('description', project.description)
    project.github_link = data.get('github_link', project.github_link)
    project.poster_url = data.get('poster_url', project.poster_url)

    db.session.commit()
    return jsonify(project.to_dict()), 200

# Delete a Project
@api_bp.route('/projects/<int:project_id>', methods=['DELETE'])
@token_required
def delete_project(current_user, project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted successfully'}), 200

# Get All Cohorts
@api_bp.route('/cohorts', methods=['GET'])
@token_required
def get_cohorts(current_user):
    cohorts = Cohort.query.all()
    if not cohorts:
        return jsonify({"message": "No cohorts found"}), 404

    return jsonify([{
        'id': cohort.id,
        'name': cohort.name,
        'description': cohort.description
    } for cohort in cohorts]), 200

# Create New Cohort
@api_bp.route('/cohorts', methods=['POST'])
@token_required
def create_cohort(current_user):
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')

    new_cohort = Cohort(
        name=name,
        description=description
    )
    db.session.add(new_cohort)
    db.session.commit()
    return jsonify(new_cohort.to_dict()), 201

# Get All Classes
@api_bp.route('/classes', methods=['GET'])
@token_required
def get_classes(current_user):
    cohort_id = request.args.get('cohort_id')
    if cohort_id:
        classes = Class.query.filter_by(cohort_id=cohort_id).all()
    else:
        classes = Class.query.all()

    return jsonify([cls.to_dict() for cls in classes]), 200

# Create New Class
@api_bp.route('/classes', methods=['POST'])
@token_required
def create_class(current_user):
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    cohort_id = data.get('cohort_id')

    new_class = Class(
        name=name,
        description=description,
        cohort_id=cohort_id
    )
    db.session.add(new_class)
    db.session.commit()
    return jsonify(new_class.to_dict()), 201

# Get All Project Members
@api_bp.route('/project_members', methods=['GET'])
@token_required
def get_project_members(current_user):
    project_members = ProjectMember.query.all()
    return jsonify([pm.to_dict() for pm in project_members]), 200

# Create a Project Member
@api_bp.route('/project_members', methods=['POST'])
@token_required
def create_project_member(current_user):
    data = request.get_json()
    project_id = data.get('project_id')
    user_id = data.get('user_id')

    new_project_member = ProjectMember(
        project_id=project_id,
        user_id=user_id
    )
    db.session.add(new_project_member)
    db.session.commit()
    return jsonify(new_project_member.to_dict()), 201

# Get All Users
@api_bp.route('/users', methods=['GET'])
@token_required
def get_users(current_user):
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

# Delete a User
@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, user_id):
    user = User.query.get_or_404(user_id)

    # Reassign user's projects to another user before deleting the user
    admin_user = User.query.filter_by(email='adminuser1@example.com').first()
    if not admin_user:
        return jsonify({'message': 'Admin user not found for reassignment'}), 404

    for project in user.projects:
        project.owner_id = admin_user.id

    db.session.commit()

    # Delete user's project memberships
    ProjectMember.query.filter_by(user_id=user_id).delete()

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200

# Create New Cohort with Classes
@api_bp.route('/cohorts_with_classes', methods=['POST'])
@token_required
def create_cohort_with_classes(current_user):
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    classes = data.get('classes', [])

    new_cohort = Cohort(
        name=name,
        description=description
    )
    
    try:
        db.session.add(new_cohort)
        db.session.flush()  # To get cohort_id for class association
        
        for cls in classes:
            new_class = Class(
                name=cls['name'],
                description=cls['description'],
                cohort_id=new_cohort.id
            )
            db.session.add(new_class)

        db.session.commit()
        return jsonify(new_cohort.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({'error': 'Failed to create cohort with classes'}), 500

# Delete a Cohort and Everything in It
@api_bp.route('/cohorts/<int:cohort_id>', methods=['DELETE'])
@token_required
def delete_cohort(current_user, cohort_id):
    cohort = Cohort.query.get_or_404(cohort_id)
    
    try:
        # Delete all projects associated with the classes in the cohort
        classes = Class.query.filter_by(cohort_id=cohort_id).all()
        for cls in classes:
            projects = Project.query.filter_by(class_id=cls.id).all()
            for project in projects:
                db.session.delete(project)
        
        # Delete all classes in the cohort
        Class.query.filter_by(cohort_id=cohort_id).delete()

        # Finally, delete the cohort itself
        db.session.delete(cohort)
        db.session.commit()
        return jsonify({'message': 'Cohort and all associated classes and projects deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete cohort'}), 500
