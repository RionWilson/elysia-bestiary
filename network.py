
import os
from contextlib import contextmanager
from flask import Flask, abort, jsonify, redirect, render_template, request
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from werkzeug.utils import secure_filename

# generate file paths
BASE_DIR = os.path.abspath(__file__).rsplit(os.sep, 1)[0]
STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOAD_DIR = os.path.join(STATIC_DIR, 'upload')

# flask configuration
app = Flask(__name__)
app.static_folder = STATIC_DIR
app.static_url_path = ""
app.secret_key = "welcometothecumzone"
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR

VALID_EXTENSIONS = ("jpg", "jpeg", "jfif", "png", "webp", "gif")

# sqlalchemy configuration
engine = create_engine("sqlite:///network.db")
Base = declarative_base()

class Users(Base):

    __tablename__ = "users"

    name = Column(String(32), primary_key=True)
    password = Column(String(32))

class Network(Base):

    __tablename__ = "network"

    address = Column(String(15), primary_key=True)
    status = Column(String(5), default="GUEST")
    login_attempts = Column(Integer, default=0)
    views = Column(Integer, default=0)

Base.metadata.create_all(engine)
session = sessionmaker(bind=engine)

@contextmanager
def get_session():

    db = session()
    try:
        yield db
    finally:
        db.close()

MAX_ATTEMPTS = 5
GUEST_LIMIT = 10

# utility functions
def verify_client(client_ip):
    with get_session() as db:
        entry = db.get(Network, client_ip)
        if entry.status == "WHITE":
            return True
        else:
            return False

@app.before_request
def network_firewall():

    client_ip = request.remote_addr

    # manage connections
    with get_session() as db:
        entry = db.get(Network, client_ip)
        if entry:
            # filter blacklisted
            if entry.status == "BLACK":
                return abort(403)
        else:
            # handle unknown
            entry = Network(address=client_ip)
            db.add(entry)
            db.commit()
        # increment view count
        if entry.status == "GUEST" and entry.views >= GUEST_LIMIT - 1:
            entry.status = "BLACK"
            entry.views = GUEST_LIMIT
            db.commit()
            return abort(403)
        else:
            entry.views += 1
            db.commit()

@app.route("/")
def home_page():

    client_ip = request.remote_addr

    if verify_client(client_ip):
        # render bestiary page
        return render_template("index.html")
    else:
        return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login_page():

    client_ip = request.remote_addr

    if verify_client(client_ip):
        # redirect whitelisted
        return redirect("/")
    elif request.method == "POST":
        # verify login attempt
        with get_session() as db:
            entry = db.get(Network, client_ip)
            user = db.get(Users, request.form["username"])
            if user and request.form["password"] == user.password:
                # successful attempt
                entry.status = "WHITE"
                db.commit()
                return redirect("/")
            elif entry.login_attempts >= MAX_ATTEMPTS - 1:
                # failure limit exceeded
                entry.status = "BLACK"
                entry.login_attempts = 5
                db.commit()
                return abort(403)
            else:
                # failed attempt
                entry.login_attempts += 1
                db.commit()
                return redirect("/login")
    else:
        # render login page
        return render_template("login.html")

@app.route("/upload", methods=["POST"])
def upload_image():

    client_ip = request.remote_addr

    if verify_client(client_ip) is False:
        # prevent guest access
        return abort(403)
    elif request.method == "POST":
        # filter failed uploads
        if "entry" not in request.form or "file" not in request.files:
            return jsonify({"status": "error", "message": "Invalid File!"})
        entry = request.form["entry"]
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"status": "error", "message": "Invalid File!"})
        extension = file.filename.rsplit(".")[1]
        if extension not in VALID_EXTENSIONS:
            return jsonify({"status": "error", "message": "Invalid File!"})
        try:
            sanitized = secure_filename(f"{entry}.{extension}")
            file.save(os.path.join(UPLOAD_DIR, sanitized))
            return jsonify({"status": "success", "message": "Upload Success!"})
        except:
            return jsonify({"status": "error", "message": "Upload Failed!"})

if __name__ == "__main__":

    # init flask server
    app.run(debug=False, host="0.0.0.0", port="8000")
