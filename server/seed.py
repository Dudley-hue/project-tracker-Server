import json
from app import create_app, db
from models import User, Role, Project, Cohort, ProjectMember, Class
from werkzeug.security import generate_password_hash

def load_data_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data

def import_users(data):
    users = data.get('users', [])
    for user_data in users:
        password_hash = user_data.get('password_hash', generate_password_hash('default_password'))
        user = User(
            id=user_data['id'],
            username=user_data['username'],
            email=user_data['email'],
            password_hash=password_hash,
            role_id=user_data.get('role_id', 2)
        )
        db.session.add(user)
    db.session.commit()

def import_cohorts(data):
    cohorts = data.get('cohorts', [])
    for cohort_data in cohorts:
        cohort = Cohort(
            id=cohort_data['id'],
            name=cohort_data['name'],
            description=cohort_data['description']
        )
        db.session.add(cohort)
    db.session.commit()

def import_classes(data):
    classes = data.get('classes', [])
    for class_data in classes:
        class_ = Class(
            id=class_data['id'],
            name=class_data['name'],
            description=class_data['description'],
            cohort_id=class_data['cohort_id']
        )
        db.session.add(class_)
    db.session.commit()

def import_projects(data):
    projects = data.get('projects', [])
    for project_data in projects:
        project = Project(
            id=project_data['id'],
            name=project_data['name'],
            description=project_data['description'],
            owner_id=project_data['owner_id'],
            github_link=project_data['github_link'],
            class_id=project_data['class_id'],
            poster_url=project_data.get('poster_url')
        )
        db.session.add(project)
    db.session.commit()

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        data = load_data_from_json('data.json')
        import_users(data)
        import_cohorts(data)
        import_classes(data)
        import_projects(data)

        print("Data imported successfully!")
