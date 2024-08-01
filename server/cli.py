import click
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Project, Cohort, ProjectMember, ProjectCohort, Role
from app import db
from flask_jwt_extended import create_access_token, decode_token
from functools import wraps

def get_role_id_by_name(role_name):
    """Get the role ID by role name."""
    role = Role.query.filter_by(name=role_name).first()
    if role:
        return role.id
    return None

def get_current_user_role(token):
    """Get the current user's role from the token."""
    try:
        decoded_token = decode_token(token)
        return decoded_token['sub']['role_id']
    except Exception as e:
        click.echo(f"Error decoding token: {e}")
        return None

def role_required(required_role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = kwargs.get('token', None)
            if not token:
                click.echo("Missing token")
                return

            role_id = get_current_user_role(token)
            if not role_id:
                click.echo("Invalid token")
                return

            user_role = Role.query.get(role_id).name
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
            click.echo(f"JWT Token: {token}")
        else:
            click.echo('Invalid email or password')

@app.cli.command('create-project')
@click.argument('name')
@click.argument('description')
@click.argument('github_link')
@click.argument('owner_email')
@click.argument('token')
@role_required('admin')
def create_project(name, description, github_link, owner_email, token):
    """Create a new project."""
    with app.app_context():
        owner = User.query.filter_by(email=owner_email).first()
        if not owner:
            click.echo('Owner not found')
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
@click.argument('token')
def update_project(project_id, name, description, github_link, token):
    """Update an existing project."""
    with app.app_context():
        role_id = get_current_user_role(token)
        project = Project.query.get(project_id)

        if not project:
            click.echo('Project not found')
            return

        if role_id == 1:  # Admin can update any project
            if name:
                project.name = name
            if description:
                project.description = description
            if github_link:
                if not github_link.startswith('https://github.com/'):
                    click.echo('GitHub link must start with "https://github.com/"')
                    return
                project.github_link = github_link
            db.session.commit()
            click.echo(f'Project {project_id} updated successfully')
        elif role_id == 2 and project.owner_id == User.query.filter_by(email=token).first().id:  # Student can only update their own projects
            if name:
                project.name = name
            if description:
                project.description = description
            if github_link:
                if not github_link.startswith('https://github.com/'):
                    click.echo('GitHub link must start with "https://github.com/"')
                    return
                project.github_link = github_link
            db.session.commit()
            click.echo(f'Project {project_id} updated successfully')
        else:
            click.echo('Permission denied')

@app.cli.command('delete-project')
@click.argument('project_id', type=int)
@click.argument('token')
@role_required('admin')
def delete_project(project_id, token):
    """Delete a project."""
    with app.app_context():
        project = Project.query.get(project_id)
        if not project:
            click.echo('Project not found')
            return

        db.session.delete(project)
        db.session.commit()
        click.echo(f'Project {project_id} deleted successfully')

@app.cli.command('create-cohort')
@click.argument('name')
@click.argument('description')
@click.argument('token')
@role_required('admin')
def create_cohort(name, description, token):
    """Create a new cohort."""
    with app.app_context():
        new_cohort = Cohort(name=name, description=description)
        db.session.add(new_cohort)
        db.session.commit()
        click.echo(f'Cohort {name} created successfully')

@app.cli.command('list-projects')
@click.argument('token')
def list_projects(token):
    """List all projects."""
    with app.app_context():
        role_id = get_current_user_role(token)
        if role_id not in [1, 2]:  # Both admins and students can view projects
            click.echo('Permission denied')
            return

        projects = Project.query.all()
        for project in projects:
            click.echo(f'ID: {project.id}, Name: {project.name}, Description: {project.description}, GitHub: {project.github_link}')

@app.cli.command('list-cohorts')
@click.argument('token')
def list_cohorts(token):
    """List all cohorts."""
    with app.app_context():
        role_id = get_current_user_role(token)
        if role_id not in [1, 2]:  # Both admins and students can view cohorts
            click.echo('Permission denied')
            return

        cohorts = Cohort.query.all()
        for cohort in cohorts:
            click.echo(f'ID: {cohort.id}, Name: {cohort.name}, Description: {cohort.description}')

@app.cli.command('list-project-members')
@click.argument('project_id', type=int)
@click.argument('token')
def list_project_members(project_id, token):
    """List all members of a project."""
    with app.app_context():
        role_id = get_current_user_role(token)
        if role_id not in [1, 2]:  # Both admins and students can view project members
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
@click.argument('token')
@role_required('admin')
def assign_project_cohort(project_id, cohort_id, token):
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
@click.argument('token')
@role_required('admin')
def assign_project_member(project_id, user_email, token):
    """Add a user as a member of a project."""
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

@app.cli.command('view-project-details')
@click.argument('project_id', type=int)
@click.argument('token')
def view_project_details(project_id, token):
    """View details of a specific project."""
    with app.app_context():
        role_id = get_current_user_role(token)
        project = Project.query.get(project_id)

        if not project:
            click.echo('Project not found')
            return

        click.echo(f'ID: {project.id}, Name: {project.name}, Description: {project.description}, GitHub: {project.github_link}')

@app.cli.command('view-user-details')
@click.argument('user_id', type=int)
@click.argument('token')
@role_required('admin')
def view_user_details(user_id, token):
    """View details of a specific user."""
    with app.app_context():
        user = User.query.get(user_id)
        if not user:
            click.echo('User not found')
            return

        click.echo(f'ID: {user.id}, Username: {user.username}, Email: {user.email}, Role: {Role.query.get(user.role_id).name}')

@app.cli.command('delete-user')
@click.argument('user_id', type=int)
@click.argument('token')
@role_required('admin')
def delete_user(user_id, token):
    """Delete a user."""
    with app.app_context():
        user = User.query.get(user_id)
        if not user:
            click.echo('User not found')
            return

        db.session.delete(user)
        db.session.commit()
        click.echo(f'User {user_id} deleted successfully')

