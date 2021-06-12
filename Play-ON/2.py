from flask import Flask, render_template


app = Flask(__name__)


@app.route("/")
def hello():
    return render_template("3.html")


@app.route("/about")
def sai():
    return render_template("about.html", boothu="lafda")


@app.route("/bootstrap")
def fun2():
    return render_template("bootstrap.html")


app.run(debug=True)
