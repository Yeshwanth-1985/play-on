
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

if (params["session_key"]):
    print("working")