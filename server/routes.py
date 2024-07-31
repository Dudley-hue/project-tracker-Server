from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from models import User, Project, Cohort, ProjectMember, ProjectCohort
from functools import wraps

from flask_jwt_extended import create_access_token
from app import db
from models import User, Project, Cohort, ProjectMember, ProjectCohort


# Define Blueprints
auth_bp = Blueprint('auth', __name__)
api_bp = Blueprint('api', __name__)


def role_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            identity = get_jwt_identity()
            user_role = identity['role_id']
            if user_role != role:
                return jsonify({'message': 'Access forbidden: Insufficient role'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Basic Test Route
@api_bp.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'API is working!'}), 200


# Registration Route
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role_id = data.get('role_id', 1)  # Default role_id to student

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'User already exists'}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password_hash=hashed_password, role_id=role_id)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

# Login Route
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Invalid credentials'}), 401

    access_token = create_access_token(identity={'username': user.username, 'role_id': user.role_id})
    return jsonify(access_token=access_token), 200


# Get all Projects
@api_bp.route('/projects', methods=['GET'])
@jwt_required()

# Get All Projects
@api_bp.route('/projects', methods=['GET'])

def get_projects():
    projects = Project.query.all()
    return jsonify([project.to_dict() for project in projects]), 200

# Get a Single Project
@api_bp.route('/projects/<int:project_id>', methods=['GET'])

@jwt_required()


def get_project(project_id):
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict()), 200

# Create a New Project
@api_bp.route('/projects', methods=['POST'])

@jwt_required()


def create_project():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')

    owner_id = get_jwt_identity()['user_id']

    owner_id = data.get('owner_id')

    github_link = data.get('github_link')

    new_project = Project(
        name=name,
        description=description,
        owner_id=owner_id,
        github_link=github_link
    )
    db.session.add(new_project)
    db.session.commit()
    return jsonify(new_project.to_dict()), 201


# Update a Project (Student can update only their own projects, Admin can update any project)
@api_bp.route('/projects/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    user_id = get_jwt_identity()['user_id']
    role_id = get_jwt_identity()['role_id']

    if role_id == 1 and project.owner_id != user_id:  # Student role
        return jsonify({'message': 'Access forbidden: You can only update your own projects'}), 403

    data = request.get_json()

# Update a Project
@api_bp.route('/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    

    project.name = data.get('name', project.name)
    project.description = data.get('description', project.description)
    project.github_link = data.get('github_link', project.github_link)
    
    db.session.commit()
    return jsonify(project.to_dict()), 200


# Delete a Project (Admin only)
@api_bp.route('/projects/<int:project_id>', methods=['DELETE'])
@jwt_required()
@role_required(2)  # Admin role

# Delete a Project
@api_bp.route('/projects/<int:project_id>', methods=['DELETE'])

def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted successfully'}), 200


# Get all Cohorts
@api_bp.route('/cohorts', methods=['GET'])
@jwt_required()

# Get All Cohorts
@api_bp.route('/cohorts', methods=['GET'])

def get_cohorts():
    cohorts = Cohort.query.all()
    return jsonify([{
        'id': cohort.id,
        'name': cohort.name,
        'description': cohort.description
    } for cohort in cohorts]), 200


# Create a New Cohort (Admin only)
@api_bp.route('/cohorts', methods=['POST'])
@jwt_required()
@role_required(2)  # Admin role

# Create a New Cohort
@api_bp.route('/cohorts', methods=['POST'])

def create_cohort():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')

    new_cohort = Cohort(
        name=name,
        description=description
    )
    db.session.add(new_cohort)
    db.session.commit()
    return jsonify({'id': new_cohort.id, 'name': new_cohort.name, 'description': new_cohort.description}), 201


# Get all Project Members
@api_bp.route('/project_members', methods=['GET'])
@jwt_required()

# Get All Project Members
@api_bp.route('/project_members', methods=['GET'])

def get_project_members():
    project_members = ProjectMember.query.all()
    return jsonify([{
        'project_id': pm.project_id,
        'user_id': pm.user_id
    } for pm in project_members]), 200


# Create a Project Member (Student can assign themselves, Admin can assign any user)
@api_bp.route('/project_members', methods=['POST'])
@jwt_required()
def create_project_member():
    data = request.get_json()
    project_id = data.get('project_id')
    user_id = get_jwt_identity()['user_id']
    role_id = get_jwt_identity()['role_id']
    
    if role_id == 1:  # Student role
        if data.get('user_id') != user_id:
            return jsonify({'message': 'Access forbidden: Students can only assign themselves'}), 403
    else:  # Admin role
        user_id = data.get('user_id')

# Create a Project Member
@api_bp.route('/project_members', methods=['POST'])
def create_project_member():
    data = request.get_json()
    project_id = data.get('project_id')
    user_id = data.get('user_id')


    new_project_member = ProjectMember(
        project_id=project_id,
        user_id=user_id
    )
    db.session.add(new_project_member)
    db.session.commit()
    return jsonify({
        'project_id': new_project_member.project_id,
        'user_id': new_project_member.user_id
    }), 201


# Get all Project Cohorts
@api_bp.route('/project_cohorts', methods=['GET'])
@jwt_required()

# Get All Project Cohorts
@api_bp.route('/project_cohorts', methods=['GET'])

def get_project_cohorts():
    project_cohorts = ProjectCohort.query.all()
    return jsonify([{
        'project_id': pc.project_id,
        'cohort_id': pc.cohort_id
    } for pc in project_cohorts]), 200


# Assign Projects to Cohorts (Admin only)
@api_bp.route('/project_cohorts', methods=['POST'])
@jwt_required()
@role_required(2)  # Admin role

# Assign Projects to Cohorts
@api_bp.route('/project_cohorts', methods=['POST'])

def assign_project_to_cohort():
    data = request.get_json()
    project_id = data.get('project_id')
    cohort_id = data.get('cohort_id')

    new_project_cohort = ProjectCohort(
        project_id=project_id,
        cohort_id=cohort_id
    )
    db.session.add(new_project_cohort)
    db.session.commit()
    return jsonify({
        'project_id': new_project_cohort.project_id,
        'cohort_id': new_project_cohort.cohort_id
    }), 201


# Get all Users (Admin only)
@api_bp.route('/users', methods=['GET'])
@jwt_required()
@role_required(2)  # Admin role
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

# Delete a User (Admin only)
@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@role_required(2)  # Admin role
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200

# Get Projects for a Specific User
@api_bp.route('/users/<int:user_id>/projects', methods=['GET'])
def get_user_projects(user_id):
    user = User.query.get_or_404(user_id)
    projects = Project.query.filter_by(owner_id=user_id).all()
    return jsonify([project.to_dict() for project in projects]), 200


# Register Blueprints
def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
