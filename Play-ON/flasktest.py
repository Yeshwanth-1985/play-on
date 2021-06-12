from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def Hello():
    return render_template("2.index.html")

@app.route("/about")
def sai():
    return render_template("2.about.html", boothu = "lafda")


@app.route("/bootstrap")
def fun2():
    return render_template("2.bootstrap.html")



app.run(debug=True)
