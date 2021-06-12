
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    return render_template("contact.html")


@app.route("/post")
def post():
    return render_template("post.html")


app.run(debug=True)
