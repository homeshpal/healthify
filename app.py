from flask import Flask, render_template, request, redirect, session
import sqlite3, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            weight INTEGER,
            goal TEXT
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meals(
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            food TEXT,
            calories INTEGER,
            protein INTEGER,
            carbs INTEGER,
            fats INTEGER,
            date TEXT
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS workouts(
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            exercise TEXT,
            sets INTEGER,
            reps INTEGER,
            weight INTEGER,
            date TEXT
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS progress(
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            image_path TEXT,
            date TEXT
        );
    """)
    conn.commit()

init_db()

# ---------- ROUTES ----------
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")
    return redirect("/dashboard")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        pw = request.form["password"]
        weight = request.form["weight"]
        goal = request.form["goal"]

        conn = get_db()
        conn.execute("INSERT INTO users(name,email,password,weight,goal) VALUES (?,?,?,?,?)",
                     (name, email, pw, weight, goal))
        conn.commit()
        return redirect("/login")

    return render_template("signup.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        pw = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=? AND password=?", 
                            (email, pw)).fetchone()
        if user:
            session["user_id"] = user["id"]
            return redirect("/dashboard")
        return "Invalid Credentials"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    uid = session["user_id"]
    conn = get_db()

    today = conn.execute("""
        SELECT SUM(calories) as cal, SUM(protein) as pro
        FROM meals WHERE user_id=? 
    """, (uid,)).fetchone()

    return render_template("dashboard.html",
                           calories=today["cal"] or 0,
                           protein=today["pro"] or 0)

@app.route("/meals", methods=["GET","POST"])
def meals():
    uid = session["user_id"]
    conn = get_db()

    if request.method == "POST":
        conn.execute("""
            INSERT INTO meals(user_id,food,calories,protein,carbs,fats,date)
            VALUES (?,?,?,?,?,?,date('now'))
        """, (uid,
              request.form["food"],
              request.form["calories"],
              request.form["protein"],
              request.form["carbs"],
              request.form["fats"]))
        conn.commit()

    data = conn.execute("SELECT * FROM meals WHERE user_id=?", (uid,)).fetchall()
    return render_template("meals.html", meals=data)

@app.route("/workouts", methods=["GET","POST"])
def workouts():
    uid = session["user_id"]
    conn = get_db()

    if request.method == "POST":
        conn.execute("""
            INSERT INTO workouts(user_id,exercise,sets,reps,weight,date)
            VALUES (?,?,?,?,?,date('now'))
        """, (uid,
              request.form["exercise"],
              request.form["sets"],
              request.form["reps"],
              request.form["weight"]))
        conn.commit()

    data = conn.execute("SELECT * FROM workouts WHERE user_id=?", (uid,)).fetchall()
    return render_template("workouts.html", workouts=data)

@app.route("/progress", methods=["GET","POST"])
def progress():
    uid = session["user_id"]
    conn = get_db()

    if request.method == "POST":
        img = request.files["image"]
        filename = secure_filename(img.filename)
        img.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn.execute("""
            INSERT INTO progress(user_id,image_path,date)
            VALUES (?,?,date('now'))
        """, (uid, filename))
        conn.commit()

    imgs = conn.execute("SELECT * FROM progress WHERE user_id=?", (uid,)).fetchall()
    return render_template("progress.html", images=imgs)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

app.run(debug=True)
