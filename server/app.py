
from flask import Flask


from flask import Flask, jsonify, request, render_template

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import Config

app = Flask(_name_)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

from models import User, Project, Cohort, ProjectMember, ProjectCohort
import routes  # Ensure this import comes after initializing app and db

# Register Blueprints
routes.register_blueprints(app)


if _name_ == "_main_":
    app.run(debug=True) 
    
class Cohort(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    projects = db.relationship('Project', backref='cohort', lazy=True)


# Forms
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('student', 'Student'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')
        
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

    # Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role=form.role.data)
        db.session.add(user)
        db.session.commit()
        return jsonify(message='User registered successfully'), 201
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity={'username': user.username, 'role': user.role})
        return jsonify(access_token=access_token), 200
    else:
        return jsonify(message='Invalid credentials'), 401


