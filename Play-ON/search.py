
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

if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params["local_uri"]
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["prod_uri"]

db = SQLAlchemy(app)

class Post(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=True)
    image_file = db.Column(db.String(20), nullable=True)

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template("request.html",params=params)

@app.route("/search", methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        string = request.form.get('search_string')
        print(string)
        sea="%{0}%".format(string)
        results = Post.query.filter(Post.content.like(sea)).all()
        print(results)
        return render_template("search.html", params=params, results=results)

    else:
        return render_template("request.html", params=params)


app.run(debug=True)