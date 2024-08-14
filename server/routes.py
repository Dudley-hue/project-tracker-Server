import jwt
import datetime
from functools import wraps
from flask import Blueprint, request, jsonify, session
from app import db
from models import User, Project, Cohort, Class, ProjectMember, Role
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

api_bp = Blueprint('api', __name__)
CORS(api_bp)

# Secret key for JWT encoding and decoding
SECRET_KEY = "your_secret_key_here"  # Replace with your actual secret key

# Decorator to check for valid JWT token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]
            else:
                return jsonify({'message': 'Authorization header must be Bearer token!'}), 401
        else:
            return jsonify({'message': 'Authorization header is missing!'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
            if not current_user:
                return jsonify({'message': 'User not found!'}), 404
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
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
        role = Role.query.get(role_id)
        
        if not role:
            return jsonify({'error': 'Role not found'}), 500

        new_user = User(username=username, email=email, role_id=role.id)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to register user', 'details': str(e)}), 500

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
def get_projects():
    projects = Project.query.all()
    return jsonify([project.to_dict() for project in projects]), 200

# Get Single Project
@api_bp.route('/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
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
    poster_url = data.get('poster_url', '')

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
        return jsonify({'error': 'Failed to create project', 'details': str(e)}), 500

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
    try:
        db.session.delete(project)
        db.session.commit()
        return jsonify({'message': 'Project deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete project', 'details': str(e)}), 500

# Get All Cohorts
@api_bp.route('/cohorts', methods=['GET'])
def get_cohorts():
    print("Cohorts endpoint hit")  # Debug statement
    cohorts = Cohort.query.all()
    if not cohorts:
        return jsonify({"message": "No cohorts found"}), 404

    return jsonify([{
        'id': cohort.id,
        'name': cohort.name,
        'description': cohort.description,
        'poster_url': cohort.poster_url
    } for cohort in cohorts]), 200

# Create New Cohort with Classes
@api_bp.route('/cohorts', methods=['POST'])
@token_required
def create_cohort(current_user):
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
        db.session.flush()  # Flush to get the cohort id before committing

        # Add classes to the cohort
        for cls in classes:
            new_class = Class(
                name=cls.get('name'),
                description=cls.get('description'),
                cohort_id=new_cohort.id
            )
            db.session.add(new_class)

        db.session.commit()  # Commit both cohort and classes together
        return jsonify(new_cohort.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create cohort with classes', 'details': str(e)}), 500

# Delete Cohort
@api_bp.route('/cohorts/<int:cohort_id>', methods=['DELETE'])
@token_required
def delete_cohort(current_user, cohort_id):
    cohort = Cohort.query.get_or_404(cohort_id)
    
    try:
        # Manually delete all classes and their projects before deleting the cohort
        for cls in cohort.classes:
            for project in cls.projects:
                db.session.delete(project)
            db.session.delete(cls)
        
        db.session.delete(cohort)
        db.session.commit()
        return jsonify({'message': 'Cohort and its associated classes and projects deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete cohort', 'details': str(e)}), 500



# Get All Classes
@api_bp.route('/classes', methods=['GET'])
def get_classes():
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
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role.name
    } for user in users]), 200

# Get Single User
@api_bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role.name
    }), 200
