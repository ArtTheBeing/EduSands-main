from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_gravatar import Gravatar
from sqlalchemy import *
import openai
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, URL
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('POSTGRES')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
db = SQLAlchemy(app)
key = os.environ.get('GPT')
openai.api_key = key
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class DescriptionGeneration():

    def __init__(self):
        pass
    def desc(self, topic):
        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
                {"role": "system", "content": "You are generate a petition based off of the topic given. The format will be in a 'change.org' type of format"},
                {'role': 'user', 'content': f'Generate a short description of a petition based on the topic of: {topic}, make it between 500-1000 characters, make sure to only print the description paragraph and nothing else. No "description" or anything signifying its a description'}
            ]
        )
        return(response['choices'][0]['message']['content'])

class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class EditPostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    body = TextAreaField('Body', validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class CreateUser(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register!')

class LoginUser(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register!')


##CONFIGURE TABLES

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author = relationship('User', back_populates='posts')
    title = db.Column(db.String(250), unique=True, nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    upvotes = db.Column(db.Integer, nullable=False)
    author_id = db.Column(db.String, ForeignKey('users.name'))


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password=db.Column(db.String(200), nullable=False)
    name=db.Column(db.String(1000), nullable=False, unique=True)
    posts = relationship('BlogPost', back_populates='author')

with app.app_context():
     db.create_all()

@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts, logged_in=current_user.is_authenticated)


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = CreateUser()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        

        user = User(
            email = form.email.data,
            name = form.username.data,
            password = generate_password_hash(form.password.data, salt_length=8)
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form, logged_in=current_user.is_authenticated)


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginUser()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('get_all_posts'))
        else:
            flash('Wrong password')
    return render_template("login.html", form=form, logged_in=current_user.is_authenticated, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>")
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    return render_template("post.html", post=requested_post, logged_in=current_user.is_authenticated, current_user=current_user)


@app.route("/about")
def about():
    return render_template("about.html", logged_in=current_user.is_authenticated)


@app.route("/contact")
def contact():
    return render_template("contact.html", logged_in=current_user.is_authenticated)


@app.route("/new-post", methods=['GET', 'POST'])
def add_new_post():
    if current_user.is_authenticated:
        form = CreatePostForm()
        if form.validate_on_submit():
            d = DescriptionGeneration()
            new_post = BlogPost(
                title=form.title.data,
                body=d.desc(form.title.data),
                author=current_user,
                date=date.today().strftime("%B %d, %Y"),
                upvotes = 0
            )
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for("get_all_posts"))
    else:
        return 'Please log in'
    return render_template("make-post.html", form=form, current_user=current_user)


@app.route("/edit-post/<int:post_id>", methods=['POST', 'GET'])
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = EditPostForm(
        title=post.title,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, logged_in=current_user.is_authenticated)

@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    if current_user.name == post_to_delete.author_id:
        db.session.delete(post_to_delete)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    else:
        return(f'You are not the appropriate user {current_user.name} and {post_to_delete.author_id}')
        

if __name__ == "__main__":
    app.run(debug=True)
    
    
