from flask import Blueprint, request, jsonify
from app import db
from models import User, Project, Cohort, Class, ProjectMember

# Define Blueprints
api_bp = Blueprint('api', __name__)

# Test Route
@api_bp.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'API is working!'}), 200

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
def create_project():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    github_link = data.get('github_link')
    owner_id = data.get('owner_id')  # Now you must provide owner_id in the request
    class_id = data.get('class_id')  # Include class_id in the request data

    new_project = Project(
        name=name,
        description=description,
        owner_id=owner_id,
        github_link=github_link,
        class_id=class_id
    )
    db.session.add(new_project)
    db.session.commit()
    return jsonify(new_project.to_dict()), 201

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

# Delete a Project
@api_bp.route('/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted successfully'}), 200

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
        'description': cohort.description
    } for cohort in cohorts]), 200


# Create New Cohort
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
def create_class():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    cohort_id = data.get('cohort_id')  # Include cohort_id in the request data

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
def get_project_members():
    project_members = ProjectMember.query.all()
    return jsonify([{
        'project_id': pm.project_id,
        'user_id': pm.user_id
    } for pm in project_members]), 200

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

# Get All Users
@api_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

# Delete a User
@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
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
