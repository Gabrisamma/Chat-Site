import sqlite3

from flask import Flask, redirect, render_template, session, request
from flask_session import Session
from helpers import apology, login_required
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["TEMPLATES_AUTO_RELOAD"] = True
Session(app)
users = dict()
statuses = list()

@app.route("/")
@login_required
def index():
    friends = list()
    if request.method == "POST":
        pass
    else:
        with sqlite3.connect("database.db") as con:
            db = con.cursor()

            rows = db.execute('SELECT * FROM friends WHERE (user_one_id = :id OR user_two_id = :id) AND status = 1',
                                {"id" : session["user_id"]}).fetchall()
            for row in rows:
                if row[0] == session["user_id"]:
                    friends.append(db.execute('SELECT username FROM users WHERE id = :id', {"id" : row[1]}).fetchone())
                elif row[1] == session["user_id"]:
                    friends.append(db.execute('SELECT username FROM users WHERE id = :id', {"id" : row[0]}).fetchone())

        return render_template("index.html", friends=friends)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        with sqlite3.connect("database.db") as con:
            db = con.cursor()
            user = db.execute('SELECT * FROM users WHERE username = :username', {"username" : username}).fetchone()
            
            if user is None:
                return apology("Username not registered", 403)
            if not check_password_hash(user[2], password):
                return apology("Invalid password", 403)

            session["user_id"] = user[0]
    else:
        return render_template("login.html")
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()

    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username =request.form.get("username") 
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        
        with sqlite3.connect("database.db") as con:
            db = con.cursor()
            user = db.execute('SELECT * FROM users WHERE username = :username', {"username" : username})

            if password != confirm:
                return apology("Passwords must match", 403)
            if not user:
                return apology("Username already in use", 403)

            db.execute('INSERT INTO users (username, hash) VALUES (?, ?)', (username, generate_password_hash(password)))
    else:
        return render_template("register.html")
    return redirect("/")


@app.route("/add-friend", methods=["GET", "POST"])
@login_required
def add_friend():
    global users
    global statuses

    if request.method == "POST":
        with sqlite3.connect("database.db") as con:
            db = con.cursor()

            if request.form["form"] == "form1":
                search = request.form.get("search")

                # Query users with username that starts with what was searched
                users = db.execute('SELECT * FROM users WHERE username LIKE :username', {"username" : search + "%"}).fetchall()
                
                # For each user, query it's status with current user (if friend or not)
                for user in users:
                    statuses.append(db.execute('SELECT * FROM friends WHERE (user_one_id = :user_one_id AND user_two_id = :user_two_id) OR (user_one_id = :user_two_id AND user_two_id = :user_one_id)',
                                                {"user_one_id" : session["user_id"], "user_two_id" : user[0]}).fetchone())                       

            else:
                user_one_id = session["user_id"]
                user_two_id = int(request.form.get("button"))
                
                if user_one_id > user_two_id:
                    user_one_id, user_two_id = user_two_id, user_one_id
                
                if request.form["form"] == "form2":

                    ''' FRIEND STATUS:
                        0: Pending
                        1: Accepted
                        2: Blocked'''
                    # Add row to table "friends" when you send a friend request (status = 0)
                    db.execute('INSERT INTO friends (user_one_id, user_two_id, status, action_user_id) SELECT * FROM (SELECT :user_one_id, :user_two_id, 0, :action_user_id) WHERE NOT EXISTS (SELECT status FROM friends WHERE user_one_id = :user_one_id AND user_two_id = :user_two_id)',
                                {"user_one_id" : user_one_id, "user_two_id" : user_two_id, "action_user_id" : session["user_id"]})

                if request.form["form"] == "form3":
                    # Update row in table friends where relation between current user and friend is stored
                    db.execute('UPDATE friends SET status = 1, action_user_id = :action_user_id WHERE user_one_id = :user_one_id AND user_two_id = :user_two_id',
                                {"user_one_id" : user_one_id, "user_two_id" : user_two_id, "action_user_id" : session["user_id"]})
            
            # Query all friend requests received
            # Where status = 0 and last user that made action is != current user
            received = db.execute('SELECT * FROM users WHERE id = (SELECT action_user_id FROM friends WHERE status = 0 AND (:id = user_one_id OR :id = user_two_id) AND friends.action_user_id != :id)',
                                  {"id" : session["user_id"]}).fetchall()
    else:
        with sqlite3.connect("database.db") as con:
            db = con.cursor()
            received = db.execute('SELECT * FROM users WHERE id = (SELECT action_user_id FROM friends WHERE status = 0 AND (:id = user_one_id OR :id = user_two_id) AND friends.action_user_id != :id)',
                                  {"id" : session["user_id"]}).fetchall()
        return render_template("friend.html", received=received)

    return render_template("friend.html", received=received, users=users, statuses=statuses)
        

@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    if request.method == "POST":
        pass
    else:
        return render_template("chat.html")
