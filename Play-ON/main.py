
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


class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    mes = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(50), nullable=True)


class Post(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=True)
    image_file = db.Column(db.String(20), nullable=True)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Post.query.filter_by(slug=post_slug).first()
    return render_template("post.html", params=params, post=post)


@app.route("/")
def home():
    posts = Post.query.filter_by().all()
    last= math.ceil(len(posts)/int(params["no_of_posts"]))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params["no_of_posts"]) : (page-1)*int(params["no_of_posts"])+int(params["no_of_posts"]) ]
    if (page==1):
        prev = "#"
        next = "/?page="+str(page + 1)
    elif(page==last):
        prev = "/?page="+str(page - 1)
        next = "#"
    else:
        prev = "/?page="+str(page - 1)
        next = "/?page="+str(page + 1)

    return render_template("index.html", params=params, posts=posts, prev=prev, next=next)


@app.route("/about")
def about():
    return render_template("about.html", params=params)


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")


@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params["admin_username"]):
        post = Post.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")


@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params["admin_username"]):
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename) ))
            return "Uploaded succesfully"



@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user'] == params["admin_username"]):
        posts = Post.query.all()
        return render_template("dashboard.html", params=params, posts=posts)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if(username == params["admin_username"] and password == params["admin_password"]):
            session['user'] = username
            posts = Post.query.all()
            return render_template("dashboard.html", params=params, posts=posts)

    return render_template("login.html", params=params)


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user'] == params["admin_username"]:
        if request.method == 'POST':
            title = request.form.get('title')
            tagline = request.form.get('tagline')
            content = request.form.get('content')
            slug = request.form.get('slug')
            image_file = request.form.get('image_file')
            date = datetime.now()

            if sno == "0":
                post = Post(title=title, slug=slug, content=content, tagline=tagline, image_file=image_file, date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post = Post.query.filter_by(sno=sno).first()
                post.title = title
                post.content = content
                post.tagline = tagline
                post.slug = slug
                post.date = date
                post.image_file = image_file
                db.session.commit()
                return redirect('/edit/'+sno)
        post = Post.query.filter_by(sno=sno).first()
        return render_template("edit.html", params=params, post=post)


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
        mail.send_message("New message from " + name,
                          sender=email,
                          recipients=[params["gmail_username"]],
                          body=message + "\n" + phone
                          )
    return render_template("contact.html", params=params)


app.run(debug=True)
