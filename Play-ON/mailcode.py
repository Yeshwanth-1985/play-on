
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
import json


local_server = True

with open("config.json", "r") as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.config.update(
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_PORT = "465",
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params["gmail_username"],
    MAIL_PASSWORD = params["gmail_password"]
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


@app.route("/")
def home():
    return render_template("index.html", params=params)


@app.route("/about")
def about():
    return render_template("about.html", params=params)


@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
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


@app.route("/post")
def post():
    return render_template("post.html", params=params)


app.run(debug=True)
