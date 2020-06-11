from flask import  Flask, render_template, request, url_for, flash, redirect
from flask_login import login_user, logout_user, login_required, LoginManager
from forms import LoginForm, RegisterForm
from user import User
import os
from werkzeug.security import generate_password_hash
import pymongo

app = Flask(__name__)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'


uri = 'mongodb+srv://admin:admin@cms-nano-lab-a2j1a.mongodb.net/test?retryWrites=true&w=majority'
client = pymongo.MongoClient(uri,maxPoolSize=50, connect=False)

def find_user(username):
    return client.cms.users.find_one({'_id': username})

def create_new_user(first_name, second_name, username, password):
    user = client.cms.users.insert_one({
        '_id': username,
        'password': generate_password_hash(password, method='pbkdf2:sha256')
    })
    return user.acknowledged


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        user = find_user(form.username.data)
        if user and User.validate_login(user['password'], form.password.data):
            user_obj = User(user['_id'])
            login_user(user_obj)
            flash("Logged in successfully!", category='success')
            return redirect(request.args.get("next") or url_for("write"))
        flash('Wrong username or password!', category='error')
    return render_template('login.html', title='login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST' and form.validate_on_submit():
        if find_user(form.username.data):
            flash("Username is already used!", category='error')
            return render_template('register.html', title='Register', form=form)

        ack = create_new_user(
            form.first_name,
            form.last_name.data,
            form.username.data,
            form.password.data)
        if ack:
            flash("Registered successfully!", category='success')
            return redirect(url_for('login'))
        flash("Registration is not successful!", category='error')
        
    return render_template('register.html', title='Register', form=form)

@app.route('/write')
@login_required
def write():
    return render_template('write.html')


@lm.user_loader
def load_user(username):
    u = client.cms.users.find_one({"_id": username})
    if not u:
        return None
    return User(u['_id'])

if __name__ == '__main__':
    app.debug = True
    app.secret_key = os.urandom(32)
    app.run()