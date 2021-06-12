
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
    song_lyrics= db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    song_location = db.Column(db.String(20), nullable=False)
    image_location = db.Column(db.String(30), nullable=False)


class Admins(db.Model):
    admin_no = db.Column(db.Integer, primary_key=True)
    admin_fullname = db.Column(db.String(20), nullable=False)
    admin_username = db.Column(db.String(20), nullable=False)
    admin_email = db.Column(db.String(30), nullable=False)
    admin_password = db.Column(db.String(20), nullable=False)
    admin_dob = db.Column(db.Date, nullable=False)
    admin_gender = db.Column(db.String(10), nullable=False)


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
activeusers = {}

@app.route("/")
def home():
    return render_template("main.html", params=params, username='')


@app.route("/songs/<string:username>")
def all(username):
    activeusers[username] = username
    if username in session:
        return render_template("userhome.html", params=params, username=username)
    return redirect("/")


@app.route("/searchname/<string:username>", methods=['GET', 'POST'])
def searchname(username):
    if username in session:
        if request.method == 'POST':
            category = request.form.get('category')
            keyword = request.form.get('keyword')
            if category == "movie":
                key = "%{0}%".format(keyword)
                results = Songs.query.filter(Songs.movie_name.like(key)).all()
            elif category == "song":
                key = "%{0}%".format(keyword)
                results = Songs.query.filter(Songs.song_name.like(key)).all()
            else:
                key = "%{0}%".format(keyword)
                results = Songs.query.filter(Songs.song_lyrics.like(key)).all()
            return render_template("usersongs.html", params=params, genre="Searched Songs", songs=results, username=username)
        return redirect("/songs/"+username)
    return redirect("/")


@app.route("/list/<string:username>/<string:genre>")
def songlist(username,genre):
    if username in session:
        key = "%{0}%".format(genre)
        results = Songs.query.filter(Songs.genre.like(key)).all()
        usersongs[username] = []
        usersongs[username].append(results)
        leng = len(usersongs[username])
        print(usersongs[username])
        print(usersongs[username][leng-1])
        print(results)
        return render_template("usersongs.html", params=params, genre=genre, songs=results, username=username)
    return render_template("userhome.html", username=username, params=params)


@app.route("/play/<string:username>/<string:sid>")
def play(username,sid):
    return render_template("player.html", index=sid, listlen=len(usersongs[username][0]), params=params, songs=usersongs[username][0], username=username)


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
        if Users.query.filter_by(username=username).first() or Admins.query.filter_by(admin_username=username).first():
            params["registermes"] = "username already exists, try another username"
            return render_template("register.html", params=params)
        elif Users.query.filter_by(email=email).first() or Admins.query.filter_by(admin_email=email).first():
            params["registermes"] = "email already registered, try another email"
            return render_template("register.html", params=params)
        elif password!=repassword:
            params["registermes"] = "entered passwords doesn't match, kindly recheck"
            return render_template("register.html", params=params)
        else:
            user = Users(fullname=fullname, email=email, username=username, password=password, gender=gender, dob=dob)
            db.session.add(user)
            db.session.commit()
            session[username] = username
            params["registermes"] = "Succesfully registered"
            return redirect('/songs/' + username)
    return render_template("register.html", params=params)


@app.route("/user", methods=['GET', 'POST'])
def user():
    params["registermes"] = "enter your details for login"
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if '@' in username and '.com' in username:
            if not Users.query.filter_by(email=username).first():
                params["mes"] = "account not found"
                render_template("userform.html", params=params)
            elif not Users.query.filter_by(email=username, password=password).first():
                params["mes"] = "username and password doesnt match"
                render_template("userform.html", params=params)
            else:
                details=Users.query.with_entities(Users.username).filter(Users.email==username).all()
                username=details[0][0]
                session[username] = username
                return redirect('/songs/' + username)
        else:
            if not Users.query.filter_by(username=username).first():
                params["mes"] = "account not found"
                render_template("userform.html", params=params)
            elif not Users.query.filter_by(username=username, password=password).first():
                params["mes"] = "username and password doesnt match"
                render_template("userform.html", params=params)
            else:
                session[username] = username
                return redirect('/songs/' + username)
    return render_template("userform.html", params=params)


@app.route("/logout/<string:username>")
def logout(username):
    if username in session:
        session.pop(username)
        activeusers.pop(username)
        return redirect("/")


@app.route("/password/<string:username>")
def password(username):
    if username in session:
        return render_template("password.html", params=params, username=username, message="Enter the details")


@app.route("/profile/<string:username>")
def profile(username):
    if username in session:
        user = Users.query.filter_by(username=username).first()
        return render_template("profile.html", params=params, username=username, user=user)


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


@app.route("/delete/<string:adminname>/<string:sid>", methods=['GET', 'POST'])
def delete(adminname,sid):
    if (adminname in session):
        song = Songs.query.filter_by(sid=sid).first()
        db.session.delete(song)
        db.session.commit()
    return redirect("/songdetails/"+adminname)


@app.route("/adminlogin", methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'POST':
        params["registermes"] = "enter your details for login"
        adminname = request.form.get('adminname')
        password = request.form.get('admin_password')
        if '@' in adminname and '.com' in adminname:
            print(password)
            if not Admins.query.filter_by(admin_email=adminname).first():
                params["mes"] = "account not found"
                render_template("adminlogin.html", params=params)
            elif not Admins.query.filter_by(admin_email=adminname, admin_password=password).first():
                params["mes"] = "username and password doesnt match"
                render_template("adminlogin.html", params=params)
            else:
                details = Admins.query.with_entities(Admins.admin_username).filter(Admins.admin_email == adminname).all()
                print(details)
                adminname = details[0][0]
                session[adminname] = adminname
                return redirect('/dashboard/' + adminname)
        else:
            print(adminname)
            if not Admins.query.filter_by(admin_username=adminname).first():
                params["mes"] = "account not found"
                render_template("adminlogin.html", params=params)
            elif not Admins.query.filter_by(admin_username=adminname, admin_password=password).first():
                params["mes"] = "username and password doesnt match"
                render_template("adminlogin.html", params=params)
            else:
                session[adminname] = adminname
                return redirect('/dashboard/' + adminname)
    return render_template("adminlogin.html", params=params)


@app.route("/adminpassword/<string:adminname>", methods=['GET', 'POST'])
def adminpass(adminname):
    if adminname in session:
        if request.method == "POST":
            currentpassword=request.form.get('currentpassword')
            newpassword = request.form.get('newpassword')
            renewpassword = request.form.get('renewpassword')
            if Admins.query.filter_by(admin_username=adminname, admin_password=currentpassword).first():
                if newpassword==renewpassword:
                    admin = Admins.query.filter_by(admin_username=adminname).first()
                    admin.admin_password = renewpassword
                    db.session.commit()
                    render_template("adminpassword.html", params=params, adminname=adminname, message="Password succesfully changed")
                render_template("adminpassword.html", params=params, adminname=adminname, message="Entered New Password doesn't match with confirm new password, please recorrect")
            render_template("adminpassword.html", params=params, adminname=adminname, message="Current password doesn't with the password in our database")
        return render_template("adminpassword.html", params=params, adminname=adminname, message="enter the details")
    return redirect("/adminlogin")


@app.route("/dashboard/<string:adminname>", methods=['GET', 'POST'])
def dashboard(adminname):
    adminsongs = Songs.query.all()
    adminusers = Users.query.all()
    adminmessages = Contact.query.all()
    admindetails = Admins.query.all()
    if (adminname in session):
        return render_template("dashboard.html",adminscount = len(admindetails), userscount=len(adminusers), activeusers=len(activeusers), totalsongs=len(adminsongs), messagescount=len(adminmessages), params=params, adminname=adminname)
    return render_template("adminlogin.html", params=params)


@app.route("/userdetails/<string:adminname>")
def userdetails(adminname):
    if (adminname in session):
        adminusers = Users.query.all()
        return render_template("userdetails.html", adminname=adminname, users=adminusers, params=params)
    return redirect("/dashboard/"+adminname)


@app.route("/songdetails/<string:adminname>")
def songdetails(adminname):
    if (adminname in session):
        adminsongs = Songs.query.all()
        return render_template("songdetails.html", adminname=adminname, songs=adminsongs, params=params)
    return redirect("/dashboard/"+adminname)


@app.route("/usermessages/<string:adminname>")
def messagedetails(adminname):
    if (adminname in session):
        adminmessages = Contact.query.all()
        return render_template("usermessages.html", adminname=adminname, users = adminmessages , params=params)
    return redirect("/dashboard/"+adminname)


@app.route("/admindetails/<string:adminname>")
def admindetails(adminname):
    if (adminname in session):
        admins = Admins.query.all()
        return render_template("admindetails.html", admins=admins, adminname=adminname, params=params)
    return redirect("/dashboard/"+adminname)


@app.route("/addadmin/<string:adminname>", methods=['GET', 'POST'])
def addadmin(adminname):
    if(adminname in session and adminname==params["mainadmin"]):
        params["registermes"] = "enter the admin details"
        if request.method == 'POST':
            fullname = request.form.get('fullname')
            email = request.form.get('email')
            username = request.form.get('username')
            password = request.form.get('password')
            gender = request.form.get('gender')
            dob = request.form.get('dob')
            repassword = request.form.get('repassword')
            if Users.query.filter_by(username=username).first() or Admins.query.filter_by(admin_username=username).first():
                params["registermes"] = "username already exists, try another username"
                return render_template("addadmin.html", adminname=adminname, params=params)
            elif Users.query.filter_by(email=email).first() or Admins.query.filter_by(admin_email=email).first():
                params["registermes"] = "email already registered, try another email"
                return render_template("addadmin.html", adminname=adminname, params=params)
            elif password != repassword:
                params["registermes"] = "entered passwords doesn't match, kindly recheck"
                return render_template("addadmin.html", adminname=adminname, params=params)
            else:
                admin = Admins(admin_fullname=fullname, admin_email=email, admin_username=username, admin_password=password, admin_gender=gender, admin_dob=dob)
                db.session.add(admin)
                db.session.commit()
                params["registermes"] = "Succesfully added"
                return redirect('/dashboard/' + adminname)
        return render_template("addadmin.html", adminname=adminname, params=params)


@app.route("/userdelete/<string:adminname>/<string:uid>", methods=['GET', 'POST'])
def deleteuser(adminname,uid):
    if (adminname in session):
        user = Users.query.filter_by(uid=uid).first()
        db.session.delete(user)
        db.session.commit()
    return redirect("/userdetails/"+adminname)


@app.route("/admindelete/<string:adminname>/<string:no>", methods=['GET', 'POST'])
def deleteadmin(adminname,no):
    if (adminname in session and adminname==params["mainadmin"]):
        admin = Admins.query.filter_by(admin_no=no).first()
        db.session.delete(admin)
        db.session.commit()
    return redirect("/admindetails/"+adminname)


@app.route("/messagedelete/<string:adminname>/<string:sno>", methods=['GET', 'POST'])
def deletemessage(adminname,sno):
    if (adminname in session):
        message = Contact.query.filter_by(sno=sno).first()
        db.session.delete(message)
        db.session.commit()
    return redirect("/usermessages/"+adminname)


@app.route("/add/<string:adminname>", methods=['GET', 'POST'])
def add(adminname):
    if adminname in session:
        if request.method == 'POST':
            song_name = request.form.get('song_name')
            movie_name = request.form.get('movie_name')
            slug = request.form.get('slug')
            song_location = request.form.get('song_location')
            genre = request.form.get('genre')
            song = Songs(song_name=song_name, genre=genre, slug=slug, movie_name=movie_name, song_location=song_location)
            db.session.add(song)
            db.session.commit()
        return render_template("add.html", adminname=adminname, params=params)


@app.route("/uploadsong/<string:adminname>")
def upload(adminname):
    if (adminname in session):
        return render_template("upload.html", adminname=adminname, params=params)


@app.route("/uploader/<string:adminname>", methods=['GET', 'POST'])
def uploader(adminname):
    if (adminname in session):
        if request.method == 'POST':
            f = request.files['file']
            if f.filename != '':
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename) ))
    return render_template("upload.html", adminname=adminname, params=params)


@app.route("/searchsong", methods=['GET', 'POST'])
def search_song():
    if params["session_user"] in session:
        if request.method == 'POST':
            song_name = request.form.get('song_name')
            key = "%{0}%".format(song_name)
            results = Songs.query.filter(Songs.song_name.like(key)).all()
            return render_template("searched_songs.html", params=params, results=results, username=username)


@app.route("/edit/<string:adminname>/<string:sid>", methods=['GET', 'POST'])
def edit(adminname,sid):
    if adminname in session:
        if request.method == 'POST':
            print(adminname)
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
            return redirect('/edit/' + adminname + "/" + sid)
        song = Songs.query.filter_by(sid=sid).first()
        return render_template("edit.html", adminname=adminname, params=params, song=song)
    return render_template("adminlogin.html", params=params)


@app.route("/about/")
def about():
    return render_template("about.html", params=params, username='')


@app.route("/about/<string:username>")
def aboutifuserin(username):
    return render_template("about.html", params=params, username=username)


@app.route("/adminlogout/<string:adminname>")
def adminlogout(adminname):
    if adminname in session:
        session.pop(adminname)
        return redirect("/")
    return render_template("adminlogin.html", params=params)


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


app.run(debug=True)
