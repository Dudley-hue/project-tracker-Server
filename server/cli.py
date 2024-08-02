import json
import click
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Project,Classroom,ProjectClassroom, Cohort, ProjectMember, ProjectCohort, Role
from app import db
from flask_jwt_extended import create_access_token, decode_token
from functools import wraps
import os

CONFIG_FILE = 'config.json'

def read_token():
    """Read the token from the config file."""
    try:
        with open(CONFIG_FILE, 'r') as file:
            config = json.load(file)
            return config.get('jwt_token')
    except Exception as e:
        click.echo(f"Error reading token from config file: {e}")
        return None

def write_token(token):
    """Write the token to the config file."""
    try:
        with open(CONFIG_FILE, 'w') as file:
            json.dump({"jwt_token": token}, file)
    except Exception as e:
        click.echo(f"Error writing token to config file: {e}")

def get_role_id_by_name(role_name):
    """Get the role ID by role name."""
    role = Role.query.filter_by(name=role_name).first()
    return role.id if role else None

def get_current_user():
    """Get the current user from the stored token."""
    token = read_token()
    if not token:
        click.echo("Token not found")
        return None

    try:
        decoded_token = decode_token(token)
        user_id = decoded_token['sub']['id']
        user = User.query.get(user_id)
        return user
    except Exception as e:
        click.echo(f"Error decoding token: {e}")
        return None

def get_current_user_role():
    """Get the current user's role from the stored token."""
    user = get_current_user()
    if not user:
        return None
    return user.role.name

def role_required(required_role):
    """Decorator to require a specific user role."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_role = get_current_user_role()
            if not user_role:
                click.echo("Invalid or missing token")
                return

            if user_role != required_role:
                click.echo(f"Access forbidden: {user_role} cannot perform this action")
                return

            return func(*args, **kwargs)
        return wrapper
    return decorator

@app.cli.command('register')
@click.argument('username')
@click.argument('email')
@click.argument('password')
@click.argument('role_name')
def register(username, email, password, role_name):
    """Register a new user."""
    with app.app_context():
        if User.query.filter_by(email=email).first():
            click.echo('User already exists')
            return
        
        role_id = get_role_id_by_name(role_name)
        if role_id is None:
            click.echo(f'Role {role_name} not found')
            return

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed_password, role_id=role_id)
        db.session.add(new_user)
        db.session.commit()
        click.echo(f'User {username} registered successfully')

@app.cli.command('login')
@click.argument('email')
@click.argument('password')
def login(email, password):
    """Login a user."""
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            token = create_access_token(identity={'id': user.id, 'role_id': user.role_id})
            write_token(token)
            click.echo(f"JWT Token stored successfully")
        else:
            click.echo('Invalid email or password')

@app.cli.command('logout')
def logout():
    """Log out the current user by removing the stored token."""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        click.echo('Logged out successfully')
    else:
        click.echo('No token found to log out')

@app.cli.command('create-project')
@click.argument('name')
@click.argument('description')
@click.argument('github_link')
@click.argument('owner_email')
@role_required('admin')
def create_project(name, description, github_link, owner_email):
    """Create a new project."""
    with app.app_context():
        owner = User.query.filter_by(email=owner_email).first()
        if not owner:
            click.echo('Owner not found')
            return

        if not github_link.startswith('https://github.com/'):
            click.echo('GitHub link must start with "https://github.com/"')
            return

        new_project = Project(name=name, description=description, owner_id=owner.id, github_link=github_link)
        db.session.add(new_project)
        db.session.commit()
        click.echo(f'Project {name} created successfully')

@app.cli.command('update-project')
@click.argument('project_id', type=int)
@click.option('--name', default=None, help='New project name')
@click.option('--description', default=None, help='New project description')
@click.option('--github_link', default=None, help='New GitHub link')
def update_project(project_id, name, description, github_link):
    """Update an existing project."""
    with app.app_context():
        user = get_current_user()
        project = Project.query.get(project_id)

        if not project:
            click.echo('Project not found')
            return

        if user.role.name == 'admin':
            # Admin can update any project
            if name:
                project.name = name
            if description:
                project.description = description
            if github_link:
                if not github_link.startswith('https://github.com/'):
                    click.echo('GitHub link must start with "https://github.com/"')
                    return
                project.github_link = github_link
        elif user.role.name == 'student' and project.owner_id == user.id:
            # Students can only update their own projects
            if name:
                project.name = name
            if description:
                project.description = description
            if github_link:
                if not github_link.startswith('https://github.com/'):
                    click.echo('GitHub link must start with "https://github.com/"')
                    return
                project.github_link = github_link
        else:
            click.echo('Permission denied')
            return

        db.session.commit()
        click.echo(f'Project {project_id} updated successfully')

@app.cli.command('delete-project')
@click.argument('project_id', type=int)
@role_required('admin')
def delete_project(project_id):
    """Delete a project."""
    with app.app_context():
        user = get_current_user()
        project = Project.query.get(project_id)

        if not project:
            click.echo('Project not found')
            return

        if user.role.name == 'admin' or project.owner_id == user.id:
            # Admins can delete any project
            # Students cannot delete their own projects
            if user.role.name == 'student':
                click.echo('Students cannot delete projects')
                return

            db.session.delete(project)
            db.session.commit()
            click.echo(f'Project {project_id} deleted successfully')
        else:
            click.echo('Permission denied')
            return

@app.cli.command('create-cohort')
@click.argument('name')
@click.argument('description')
@role_required('admin')
def create_cohort(name, description):
    """Create a new cohort."""
    with app.app_context():
        new_cohort = Cohort(name=name, description=description)
        db.session.add(new_cohort)
        db.session.commit()
        click.echo(f'Cohort {name} created successfully')

@app.cli.command('list-projects')
def list_projects():
    """List all projects."""
    with app.app_context():
        role_id = get_current_user_role()
        if role_id not in ['admin', 'student']:  # Both admins and students can view projects
            click.echo('Permission denied')
            return

        projects = Project.query.all()
        for project in projects:
            click.echo(f'ID: {project.id}, Name: {project.name}, Description: {project.description}, GitHub: {project.github_link}')

@app.cli.command('list-cohorts')
def list_cohorts():
    """List all cohorts."""
    with app.app_context():
        role_id = get_current_user_role()
        if role_id not in ['admin', 'student']:  # Both admins and students can view cohorts
            click.echo('Permission denied')
            return

        cohorts = Cohort.query.all()
        for cohort in cohorts:
            click.echo(f'ID: {cohort.id}, Name: {cohort.name}, Description: {cohort.description}')

@app.cli.command('list-project-members')
@click.argument('project_id', type=int)
def list_project_members(project_id):
    """List all members of a project."""
    with app.app_context():
        role_id = get_current_user_role()
        if role_id not in ['admin', 'student']:  # Both admins and students can view project members
            click.echo('Permission denied')
            return

        project = Project.query.get(project_id)
        if not project:
            click.echo('Project not found')
            return

        members = ProjectMember.query.filter_by(project_id=project_id).all()
        for member in members:
            user = User.query.get(member.user_id)
            click.echo(f'User ID: {user.id}, Username: {user.username}')

@app.cli.command('assign-project-cohort')
@click.argument('project_id', type=int)
@click.argument('cohort_id', type=int)
@role_required('admin')
def assign_project_cohort(project_id, cohort_id):
    """Assign a project to a cohort."""
    with app.app_context():
        project = Project.query.get(project_id)
        cohort = Cohort.query.get(cohort_id)

        if not project:
            click.echo('Project not found')
            return

        if not cohort:
            click.echo('Cohort not found')
            return

        new_project_cohort = ProjectCohort(project_id=project_id, cohort_id=cohort_id)
        db.session.add(new_project_cohort)
        db.session.commit()
        click.echo(f'Project {project_id} assigned to Cohort {cohort_id} successfully')

@app.cli.command('assign-project-member')
@click.argument('project_id', type=int)
@click.argument('user_email')
@role_required('admin')
def assign_project_member(project_id, user_email):
    """Assign a user to a project."""
    with app.app_context():
        project = Project.query.get(project_id)
        user = User.query.filter_by(email=user_email).first()

        if not project:
            click.echo('Project not found')
            return

        if not user:
            click.echo('User not found')
            return

        new_project_member = ProjectMember(project_id=project_id, user_id=user.id)
        db.session.add(new_project_member)
        db.session.commit()
        click.echo(f'User {user_email} assigned to Project {project_id} successfully')

@app.cli.command('remove-project-member')
@click.argument('project_id', type=int)
@click.argument('user_email')
@role_required('admin')
def remove_project_member(project_id, user_email):
    """Remove a user from a project."""
    with app.app_context():
        project = Project.query.get(project_id)
        user = User.query.filter_by(email=user_email).first()

        if not project:
            click.echo('Project not found')
            return

        if not user:
            click.echo('User not found')
            return

        project_member = ProjectMember.query.filter_by(project_id=project_id, user_id=user.id).first()
        if project_member:
            db.session.delete(project_member)
            db.session.commit()
            click.echo(f'User {user_email} removed from Project {project_id} successfully')
        else:
            click.echo(f'User {user_email} is not a member of Project {project_id}')

@app.cli.command('remove-project-cohort')
@click.argument('project_id', type=int)
@click.argument('cohort_id', type=int)
@role_required('admin')
def remove_project_cohort(project_id, cohort_id):
    """Remove a cohort assignment from a project."""
    with app.app_context():
        user = get_current_user()
        project = Project.query.get(project_id)
        cohort = Cohort.query.get(cohort_id)

        if not project:
            click.echo('Project not found')
            return

        if not cohort:
            click.echo('Cohort not found')
            return

        if project.owner_id != user.id:
            click.echo('You can only remove cohorts from your own projects')
            return

        project_cohort = ProjectCohort.query.filter_by(project_id=project_id, cohort_id=cohort_id).first()
        if project_cohort:
            db.session.delete(project_cohort)
            db.session.commit()
            click.echo(f'Cohort {cohort_id} removed from Project {project_id} successfully')
        else:
            click.echo(f'Cohort {cohort_id} is not assigned to Project {project_id}')
# creating the classrooms cli
@app.cli.command('create-classroom')
@click.argument('name')
@click.argument('description')
@role_required('admin')
def create_classroom(name, description):
    """Create a new classroom."""
    with app.app_context():
        new_classroom = Classroom(name=name, description=description)
        db.session.add(new_classroom)
        db.session.commit()
        click.echo(f'Classroom {name} created successfully')
@app.cli.command('list-classrooms')
def list_classrooms():
    """List all classrooms."""
    with app.app_context():
        role_id = get_current_user_role()
        if role_id not in ['admin', 'student']:
            click.echo('Permission denied')
            return

        classrooms = Classroom.query.all()
        for classroom in classrooms:
            click.echo(f'ID: {classroom.id}, Name: {classroom.name}, Description: {classroom.description}')

@app.cli.command('assign-project-classroom')
@click.argument('project_id', type=int)
@click.argument('classroom_id', type=int)
@role_required('admin')
def assign_project_classroom(project_id, classroom_id):
    """Assign a classroom to a project."""
    with app.app_context():
        project = Project.query.get(project_id)
        classroom = Classroom.query.get(classroom_id)

        if not project:
            click.echo('Project not found')
            return

        if not classroom:
            click.echo('Classroom not found')
            return

        new_project_classroom = ProjectClassroom(project_id=project_id, classroom_id=classroom_id)
        db.session.add(new_project_classroom)
        db.session.commit()
        click.echo(f'Project {project_id} assigned to Classroom {classroom_id} successfully')

@app.cli.command('remove-project-classroom')
@click.argument('project_id', type=int)
@click.argument('classroom_id', type=int)
@role_required('admin')
def remove_project_classroom(project_id, classroom_id):
    """Remove a classroom assignment from a project."""
    with app.app_context():
        user = get_current_user()
        project = Project.query.get(project_id)
        classroom = Classroom.query.get(classroom_id)

        if not project:
            click.echo('Project not found')
            return

        if not classroom:
            click.echo('Classroom not found')
            return

        if project.owner_id != user.id:
            click.echo('You can only remove classrooms from your own projects')
            return

        project_classroom = ProjectClassroom.query.filter_by(project_id=project_id, classroom_id=classroom_id).first()
        if project_classroom:
            db.session.delete(project_classroom)
            db.session.commit()
            click.echo(f'Classroom {classroom_id} removed from Project {project_id} successfully')
        else:
            click.echo(f'Classroom {classroom_id} is not assigned to Project {project_id}')