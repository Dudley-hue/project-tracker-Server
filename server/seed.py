import json
from app import create_app, db
from models import User, Role, Project, Cohort, ProjectMember, Class
from werkzeug.security import generate_password_hash

def load_data_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def seed_roles():
    if Role.query.count() == 0:
        roles = [
            Role(id=1, name='admin'),
            Role(id=2, name='student')
        ]
        db.session.bulk_save_objects(roles)
        db.session.commit()
        print("Roles seeded successfully!")

def import_users(data):
    if User.query.count() == 0:
        users = data.get('users', [])
        for user_data in users:
            password_hash = generate_password_hash('default_password')  # Set a default password
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=password_hash,
                role_id=user_data.get('role_id', 1)
            )
            db.session.add(user)
        db.session.commit()
        print("Users seeded successfully!")
    else:
        print("Users already exist, skipping seeding.")

def import_cohorts(data):
    if Cohort.query.count() == 0:
        cohorts = data.get('cohorts', [])
        db.session.bulk_insert_mappings(Cohort, cohorts)
        db.session.commit()
        print("Cohorts seeded successfully!")
    else:
        print("Cohorts already exist, skipping seeding.")

def import_classes(data):
    if Class.query.count() == 0:
        classes = data.get('classes', [])
        db.session.bulk_insert_mappings(Class, classes)
        db.session.commit()
        print("Classes seeded successfully!")
    else:
        print("Classes already exist, skipping seeding.")

def import_projects(data):
    if Project.query.count() == 0:
        projects = data.get('projects', [])
        db.session.bulk_insert_mappings(Project, projects)
        db.session.commit()
        print("Projects seeded successfully!")
    else:
        print("Projects already exist, skipping seeding.")

def generate_project_members():
    if ProjectMember.query.count() == 0:
        users = User.query.filter_by(role_id=2).all()  # Only students should be project members
        projects = Project.query.all()
        for project in projects:
            for user in users:
                project_member = ProjectMember(project_id=project.id, user_id=user.id)
                db.session.add(project_member)
        db.session.commit()
        print("Project members generated successfully!")
    else:
        print("Project members already exist, skipping generation.")

if __name__ == "__main__":
    app = create_app()  # Initialize the Flask app
    with app.app_context():  # Ensure the app context is active
        db.drop_all()  # Drops all tables to ensure a fresh start
        db.create_all()  # Creates all tables based on models

        seed_roles()  # Seed roles first since other data depends on roles

        data = load_data_from_json('data.json')
        import_users(data)  # Import users after roles are seeded
        import_cohorts(data)
        import_classes(data)
        import_projects(data)
        generate_project_members()  # Generate project members after all other data is seeded

        print("Data imported and seeded successfully!")
