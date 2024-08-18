import click
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Project, Role, Class, Cohort, ProjectMember
from app import db

def get_role_id_by_name(role_name):
    """Get the role ID by role name."""
    role = Role.query.filter_by(name=role_name).first()
    if role:
        return role.id
    return None

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

@app.cli.command('create-cohort')
@click.argument('name')
@click.argument('description')
def create_cohort(name, description):
    """Create a new cohort."""
    with app.app_context():
        new_cohort = Cohort(name=name, description=description)
        db.session.add(new_cohort)
        db.session.commit()
        click.echo(f'Cohort {name} created successfully')

@app.cli.command('create-project')
@click.argument('name')
@click.argument('description')
@click.argument('github_link')
@click.argument('owner_email')
@click.argument('class_id')
def create_project(name, description, github_link, owner_email, class_id):
    """Create a new project."""
    with app.app_context():
        owner = User.query.filter_by(email=owner_email).first()
        if not owner:
            click.echo('Owner not found')
            return

        new_project = Project(name=name, description=description, owner_id=owner.id, github_link=github_link, class_id=class_id)
        db.session.add(new_project)
        db.session.commit()
        click.echo(f'Project {name} created successfully')

@app.cli.command('list-projects')
def list_projects():
    """List all projects."""
    with app.app_context():
        projects = Project.query.all()
        for project in projects:
            click.echo(f'ID: {project.id}, Name: {project.name}, Description: {project.description}, GitHub: {project.github_link}')

@app.cli.command('create-class')
@click.argument('name')
@click.argument('description')
@click.argument('cohort_id')
def create_class(name, description, cohort_id):
    """Create a new class."""
    with app.app_context():
        new_class = Class(name=name, description=description, cohort_id=cohort_id)
        db.session.add(new_class)
        db.session.commit()
        click.echo(f'Class {name} created successfully')

@app.cli.command('list-classes')
def list_classes():
    """List all classes."""
    with app.app_context():
        classes = Class.query.all()
        for cls in classes:
            click.echo(f'ID: {cls.id}, Name: {cls.name}, Description: {cls.description}')

@app.cli.command('assign-user-to-class')
@click.argument('user_email')
@click.argument('class_id')
def assign_user_to_class(user_email, class_id):
    """Assign a user to a class."""
    with app.app_context():
        user = User.query.filter_by(email=user_email).first()
        if not user:
            click.echo('User not found')
            return

        class_ = Class.query.get(class_id)
        if not class_:
            click.echo('Class not found')
            return

        user.class_id = class_id
        db.session.commit()
        click.echo(f'User {user.username} assigned to class {class_.name} successfully')

@app.cli.command('delete-user')
@click.argument('user_id')
def delete_user(user_id):
    """Delete a user."""
    with app.app_context():
        user = User.query.get_or_404(user_id)
        
        # Reassign projects to another user (admin) before deleting the user
        admin_user = User.query.filter_by(email='adminuser@example.com').first()
        if not admin_user:
            click.echo('Admin user not found for reassignment')
            return
        
        for project in user.projects:
            project.owner_id = admin_user.id
        
        db.session.commit()

        # Delete associated project members
        ProjectMember.query.filter_by(user_id=user.id).delete()
        
        db.session.delete(user)
        db.session.commit()
        click.echo('User deleted successfully')
