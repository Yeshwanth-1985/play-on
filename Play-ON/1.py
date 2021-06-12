
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import math
import os

local_server = True

with open("config.json", "r") as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = params["upload_location"]
app.secret_key = 'super_secret_key'


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
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20), nullable=False)


@app.route("/")
def home():
    params["session_user"] = ""
    return render_template("main.html", params=params)


@app.route("/logout")
def logout():
    session.pop(params["session_user"])
    params["session_user"] = ""
    return redirect("/")


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


@app.route("/searchsong", methods=['GET', 'POST'])
def search_song():
    if params["session_user"] in session:
        if request.method == 'POST':
            song_name = request.form.get('song_name')
            key = "%{0}%".format(song_name)
            results = Songs.query.filter(Songs.song_name.like(key)).all()
            return render_template("searched_songs.html", params=params, results=results)


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


@app.route("/about")
def about():
    return render_template("about.html", params=params)


@app.route("/adminlogout")
def adminlogout():
    session.pop('admin')
    return redirect("/dashboard")


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contact(name=name, phone_num=phone, mes=message, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()
    return render_template("contact.html", params=params)


@app.route("/registeruser", methods=['GET', 'POST'])
def register():
    params["registermes"] = "enter your details for registration"
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if Users.query.filter_by(username=username).first():
            params["registermes"] = "username already exists, try another username"
            return render_template("register.html", params=params)
        else:
            user = Users(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            params["session_user"] = username
            session[params["session_user"]] = username
            song = Songs.query.filter_by().all()
            return render_template("home.html", params=params, songs=song)
    return render_template("register.html", params=params)


@app.route("/user", methods=['GET', 'POST'])
def user():
    params["mes"] = "enter the details"
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not Users.query.filter_by(username=username).first():
            params["mes"] = "account not found"
            render_template("userlogin.html", params=params)
        elif not Users.query.filter_by(username=username, password=password).first():
            params["mes"] = "username and password doesnt match"
            render_template("userlogin.html", params=params)
        else:
            params["session_user"] = username
            session[params["session_user"]] = username
            song = Songs.query.filter_by().all()
            return render_template("home.html", params=params, songs=song)
    return render_template("userlogin.html", params=params)


@app.route("/songs")
def all():
    if params["session_user"] in session:
        song = Songs.query.filter_by().all()
        return render_template("home.html", params=params, songs=song)

app.run(debug=True)
