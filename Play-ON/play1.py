
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import math
import os
import re

local_server = True

with open("config.json", "r") as c:
    params = json.load(c)["params"]


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = params["upload_location"]
app.config['UPLOAD_EXTENSIONS'] = ['.mp3']
app.secret_key = 'super_secret_key'
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT="465",
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params["gmail_username"],
    MAIL_PASSWORD=params["gmail_password"]
)
mail = Mail(app)

if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params["local_uri"]
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["prod_uri"]

db = SQLAlchemy(app)


class Songs(db.Model):
    sid = db.Column(db.Integer, primary_key=True)
    song_name = db.Column(db.String(20), nullable=False)
    movie_name = db.Column(db.String(30), nullable=False)
    genre = db.Column(db.String(20), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    song_location = db.Column(db.String(20), nullable=False)


class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    mes = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(50), nullable=True)


class Users(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    fullname=db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(30), nullable=False)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    dob = db.Column(db.Date, nullable=False)


usersongs = {}

@app.route("/")
def home():
    return render_template("main.html", params=params, username='')


@app.route("/play/<string:username>")
def play(username):
    print(username)
    print(len(usersongs[username][0]))
    return render_template("player.html", listlen=len(usersongs[username][0]), params=params, songs=usersongs[username][0], username=username)


@app.route("/registeruser", methods=['GET', 'POST'])
def register():
    params["registermes"] = "enter your details for registration"
    if request.method == 'POST':
        fullname= request.form.get('fullname')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        gender = request.form.get('gender')
        dob = request.form.get('dob')
        repassword = request.form.get('repassword')
        #doblist = re.split('-', dob)
        #curlist = re.split('-', datetime.today().strftime('%Y-%m-%d'))
        if Users.query.filter_by(username=username).first():
            params["registermes"] = "username already exists, try another username"
            return render_template("register.html", params=params)
        elif Users.query.filter_by(email=email).first():
            params["registermes"] = "email already registered, try another email"
            return render_template("register.html", params=params)
        elif password!=repassword:
            params["registermes"] = "entered passwords doesn't match, kindly recheck"
        else:
            user = Users(fullname=fullname, email=email, username=username, password=password, gender=gender, dob=dob)
            db.session.add(user)
            db.session.commit()
            session[username] = username
            song = Songs.query.filter_by().all()
            return render_template("userhome.html", params=params, username=username)
    return render_template("register.html", params=params)


@app.route("/user", methods=['GET', 'POST'])
def user():
    params["mes"] = "enter the details"
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if '@' in username and '.com' in username:
            if not Users.query.filter_by(email=username).first():
                params["mes"] = "account not found"
                render_template("userlogin.html", params=params)
            elif not Users.query.filter_by(email=username, password=password).first():
                params["mes"] = "username and password doesnt match"
                render_template("userlogin.html", params=params)
            else:
                details=Users.query.with_entities(Users.username).filter(Users.email==username).all()
                username=details[0][0]
                session[username] = username
                song = Songs.query.filter_by().all()
                print(song[0])
                return render_template("userhome.html", params=params, songs=song, username=username)
        else:
            if not Users.query.filter_by(username=username).first():
                params["mes"] = "account not found"
                render_template("userlogin.html", params=params)
            elif not Users.query.filter_by(username=username, password=password).first():
                params["mes"] = "username and password doesnt match"
                render_template("userlogin.html", params=params)
            else:
                session[username] = username
                song = Songs.query.filter_by().all()
                usersongs[username]= []
                usersongs[username].append(song)
                print(usersongs[username][0])
                print(usersongs)
                return render_template("userhome.html", params=params, songs=song, username=username)
    return render_template("userlogin.html", params=params)


@app.route("/list/<string:username>/<string:genre>")
def songlist(username,genre):
    if username in session:
        key = "%{0}%".format(genre)
        results = Songs.query.filter(Songs.genre.like(key)).all()
        print(results)

        return render_template("usersongs.html", params=params, genre=genre, songs=results, username=username)
    return render_template("userhome.html", username=username, params=params)


@app.route("/logout/<string:username>")
def logout(username):
    if username in session:
        session.pop(username)
        params["session_user"] = ""
        return redirect("/")


@app.route("/password/<string:username>")
def password(username):
    if username in session:
        return render_template("password.html", params=params, username=username, message="Enter the details")


@app.route("/changepass/<string:username>", methods=['GET', 'POST'])
def changepass(username):
    if username in session:
        currentpassword=request.form.get('currentpassword')
        newpassword = request.form.get('newpassword')
        renewpassword = request.form.get('renewpassword')
        if Users.query.filter_by(username=username, password=currentpassword).first():
            if newpassword==renewpassword:
                user = Users.query.filter_by(username=username).first()
                user.password = renewpassword
                db.session.commit()
                return render_template("password.html", params=params, username=username, message="Password succesfully changed")
            return render_template("password.html", params=params, username=username, message="Entered New Password doesn't match with confirm new password, please recorrect")
        return render_template("password.html", params=params, username=username, message="Current password doesn't with the password in our database")


@app.route("/delete/<string:sid>", methods=['GET', 'POST'])
def delete(sid):
    if ('admin' in session and session['admin'] == params["admin_username"]):
        song = Songs.query.filter_by(sid=sid).first()
        db.session.delete(song)
        db.session.commit()
    return redirect("/dashboard")


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if ('admin' in session and session['admin'] == params["admin_username"]):
        song = Songs.query.all()
        return render_template("dashboard.html", params=params, songs=song)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if(username == params["admin_username"] and password == params["admin_password"]):
            session['admin'] = username
            song = Songs.query.all()
            return render_template("dashboard.html", params=params, songs=song)
    return render_template("adminlogin.html", params=params)


@app.route("/add", methods=['GET', 'POST'])
def add():
    if 'admin' in session and session['admin'] == params["admin_username"]:
        if request.method == 'POST':
            song_name = request.form.get('song_name')
            movie_name = request.form.get('movie_name')
            slug = request.form.get('slug')
            song_location = request.form.get('song_location')
            genre = request.form.get('genre')
            song = Songs(song_name=song_name, genre=genre, slug=slug, movie_name=movie_name, song_location=song_location)
            db.session.add(song)
            db.session.commit()
        return render_template("add.html", params=params)


@app.route("/uploadsong")
def upload():
    if ('admin' in session and session['admin'] == params["admin_username"]):
        return render_template("upload.html", params=params)


@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if ('admin' in session and session['admin'] == params["admin_username"]):
        if request.method == 'POST':
            f = request.files['file']
            if f.filename != '':
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename) ))
                print("Submitted")
    return render_template("upload.html", params=params)


@app.route("/searchsong", methods=['GET', 'POST'])
def search_song():
    if params["session_user"] in session:
        if request.method == 'POST':
            song_name = request.form.get('song_name')
            key = "%{0}%".format(song_name)
            results = Songs.query.filter(Songs.song_name.like(key)).all()
            return render_template("searched_songs.html", params=params, results=results, username=username)


@app.route("/edit/<string:sid>", methods=['GET', 'POST'])
def edit(sid):
    if 'admin' in session and session['admin'] == params["admin_username"]:
        if request.method == 'POST':
            song_name = request.form.get('song_name')
            movie_name = request.form.get('movie_name')
            slug = request.form.get('slug')
            song_location = request.form.get('song_location')
            genre = request.form.get('genre')
            song = Songs.query.filter_by(sid=sid).first()
            song.song_name = song_name
            song.slug = slug
            song.genre=genre
            song.movie_name = movie_name
            song.song_location = song_location
            db.session.commit()
            return redirect('/edit/' + sid)
        song = Songs.query.filter_by(sid=sid).first()
        return render_template("edit.html", params=params, song=song)


@app.route("/about/")
def about():
    return render_template("about.html", params=params, username='')


@app.route("/about/<string:username>")
def aboutifuserin(username):
    return render_template("about.html", params=params, username=username)


@app.route("/adminlogout")
def adminlogout():
    session.pop('admin')
    return redirect("/dashboard")


@app.route("/contact/", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contact(name=name, phone_num=phone, mes=message, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()
    return render_template("contact.html", params=params, username='')


@app.route("/contact/<string:username>", methods=['GET', 'POST'])
def contactifuserin(username):
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contact(name=name, phone_num=phone, mes=message, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()
    return render_template("contact.html", params=params, username=username)


@app.route("/songs/<string:username>")
def all(username):
    if username in session:
        song = Songs.query.filter_by().all()
        print(song)
        print("byee")
        return render_template("home.html", params=params, songs=song, username=username)

app.run(debug=True)
