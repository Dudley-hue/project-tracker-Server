import click
from flask import Flask
from app import create_app, db
from models import User, Project, Cohort, ProjectMember, ProjectCohort
from werkzeug.security import generate_password_hash
import requests

app = create_app()

@app.cli.command('register')
@click.argument('username')
@click.argument('email')
@click.argument('password')
@click.argument('role_id', default=1)
def register(username, email, password, role_id):
    """Register a new user."""
    if User.query.filter_by(email=email).first():
        click.echo('User already exists')
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
    """Login a user and get a JWT token."""
    response = requests.post('http://127.0.0.1:5000/auth/login', json={'email': email, 'password': password})
    if response.status_code == 200:
        click.echo(f"JWT Token: {response.json()['access_token']}")
    else:
        click.echo('Login failed')

@app.cli.command('create-project')
@click.argument('name')
@click.argument('description')
@click.argument('github_link')
@click.argument('owner_email')
def create_project(name, description, github_link, owner_email):
    """Create a new project."""
    owner = User.query.filter_by(email=owner_email).first()
    if not owner:
        click.echo('Owner not found')
        return

    new_project = Project(name=name, description=description, owner_id=owner.id, github_link=github_link)
    db.session.add(new_project)
    db.session.commit()
    click.echo(f'Project {name} created successfully')

@app.cli.command('list-projects')
def list_projects():
    """List all projects."""
    projects = Project.query.all()
    for project in projects:
        click.echo(f'ID: {project.id}, Name: {project.name}, Description: {project.description}, GitHub: {project.github_link}')

@app.cli.command('update-project')
@click.argument('project_id', type=int)
@click.option('--name', default=None, help='New project name')
@click.option('--description', default=None, help='New project description')
@click.option('--github_link', default=None, help='New GitHub link')
def update_project(project_id, name, description, github_link):
    """Update an existing project."""
    project = Project.query.get(project_id)
    if not project:
        click.echo('Project not found')
        return

    if name:
        project.name = name
    if description:
        project.description = description
    if github_link:
        project.github_link = github_link

    db.session.commit()
    click.echo(f'Project {project_id} updated successfully')

@app.cli.command('delete-project')
@click.argument('project_id', type=int)
def delete_project(project_id):
    """Delete a project."""
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
def create_cohort(name, description):
    """Create a new cohort."""
    new_cohort = Cohort(name=name, description=description)
    db.session.add(new_cohort)
    db.session.commit()
    click.echo(f'Cohort {name} created successfully')

@app.cli.command('list-cohorts')
def list_cohorts():
    """List all cohorts."""
    cohorts = Cohort.query.all()
    for cohort in cohorts:
        click.echo(f'ID: {cohort.id}, Name: {cohort.name}, Description: {cohort.description}')

@app.cli.command('assign-project-cohort')
@click.argument('project_id', type=int)
@click.argument('cohort_id', type=int)
def assign_project_cohort(project_id, cohort_id):
    """Assign a project to a cohort."""
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

@app.cli.command('create-project-member')
@click.argument('project_id', type=int)
@click.argument('user_email')
def create_project_member(project_id, user_email):
    """Add a user as a member of a project."""
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
    click.echo(f'User {user_email} added to Project {project_id} successfully')

@app.cli.command('list-project-members')
@click.argument('project_id', type=int)
def list_project_members(project_id):
    """List all members of a project."""
    project = Project.query.get(project_id)
    if not project:
        click.echo('Project not found')
        return

    members = project.project_members
    for member in members:
        user = User.query.get(member.user_id)
        click.echo(f'User ID: {user.id}, Username: {user.username}')

if __name__ == '__main__':
    app.run()
