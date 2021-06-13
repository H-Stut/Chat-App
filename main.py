from flask import Flask,render_template,request,redirect, session
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug import debug
from models import RoomModel, UserModel,db,login, MessageModel
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_session import Session
from datetime import datetime
 
app = Flask(__name__)

app.secret_key = 'secret'
 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SECRET_TYPE"] = "secret"
app.config["SESSION_TYPE"] = "filesystem"
 
db.init_app(app)
login.init_app(app)
login.login_view = 'login'
socketio = SocketIO(app)
 
@app.before_first_request
def create_all():
    db.create_all()
     
@app.route('/chat', methods=["GET", "POST"])
@login_required
def chat():
    if request.method=="POST":
        if "join" in request.form:
            room = request.form["name"]
            password = request.form["password"]
            session["room"] = room
            session["username"] = current_user.username

            username = RoomModel.query.filter_by(username=current_user.username).all()
            roomNames = ["a"] * len(username)

            for i in range(0, len(username)):
                roomNames[i] = username[i].room_name

            name = RoomModel.query.filter_by(room_name=room).first()
            if name is not None and name.check_room_password(password):
                return redirect("/message")
            if name is None or not name.check_room_password(password):
                return render_template("chat.html", context="Incorrect room name or password", session=session, count=len(username), rooms=roomNames)
            return render_template("chat.html", session=session)
        elif "create" in request.form:
            room = request.form["name"]
            password = request.form["password"]
            session["room"] = room
            session["username"] = current_user.username

            username = RoomModel.query.filter_by(username=current_user.username).all()
            roomNames = ["a"] * len(username)

            for i in range(0, len(username)):
                roomNames[i] = username[i].room_name

            name = RoomModel.query.filter_by(room_name=room).first()
            if name is not None:
                return render_template("chat.html", context="Room name already exists did you mean to join?",  session=session, count=len(username), rooms=roomNames)
            if name is None:
                username = RoomModel.query.filter_by(username=current_user.username).all()
                if len(username) > 10:
                    return render_template("chat.html", context="You cannot create more than 10 chat rooms per account", session=session, count=len(username), rooms=roomNames)
                user = RoomModel()
                user.room_name = room
                user.username = current_user.username
                user.set_room_password(password)
                db.session.add(user)
                db.session.commit()
                print(username)
                return redirect("/message")
        elif "joinS" in request.form:
            session["room"] = request.form["joinS"]
            return redirect("/message")
        return render_template("chat.html", session=session)
    else:
        username = RoomModel.query.filter_by(username=current_user.username).all()
        roomNames = ["a"] * len(username)
        for i in range(0, len(username)):
            roomNames[i] = username[i].room_name
        return render_template('chat.html', session=session, count=len(username), rooms=roomNames)

@socketio.on("connected")
def connected(json, methods=["GET", "POST"]):
    allMessages = MessageModel.query.filter_by(room=session.get("room")).all()
    content=[""] * len(allMessages)
    authors=[""] * len(allMessages)
    time=[""] * len(allMessages)
    for i in range(0, len(allMessages)):
        content[i] = allMessages[i].content
        authors[i] = allMessages[i].author
        time[i] = allMessages[i].time

    socketio.emit('message recieved', {
        "author" : authors,
        "content" : content,
        "time" : time
        }, callback=messageReceived)

@socketio.on('message sent')
def messageReceived(json, methods=['GET', 'POST']):
    json["username"] = current_user.username

    messages = MessageModel()
    messages.room = session.get("room")
    messages.author = current_user.username
    messages.content = json["message"]
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    messages.time = current_time

    db.session.add(messages)
    db.session.commit()

    allMessages = MessageModel.query.filter_by(room=session.get("room")).all()
    content=[""] * len(allMessages)
    authors=[""] * len(allMessages)
    time=[""] * len(allMessages)
    for i in range(0, len(allMessages)):
        content[i] = allMessages[i].content
        authors[i] = allMessages[i].author
        time[i] = allMessages[i].time

    socketio.emit('message recieved', {
        "author" : authors,
        "content" : content,
        "time" : time
        }, callback=messageReceived)

@app.route("/message", methods=["POST", "GET"])
@login_required
def message():
    if request.method == "GET":
        if session["room"] == None:
            username = RoomModel.query.filter_by(username=current_user.username).all()
            roomNames = ["a"] * len(username)
            for i in range(0, len(username)):
                roomNames[i] = username[i].room_name
            return redirect("/chat")

        username = current_user.username
        room = session.get("room")
        room2 = RoomModel.query.filter_by(room_name=room).first()
        if room2 == None:
            username = RoomModel.query.filter_by(username=current_user.username).all()
            roomNames = ["a"] * len(username)
            for i in range(0, len(username)):
                roomNames[i] = username[i].room_name
            return redirect("/chat")

        owner = room2.username
        if (username == owner):
            return render_template("message.html", session=session, admin=True)
        else:
            return render_template("message.html", session=session, admin=False)
    else:
        if "rem" in request.form:
            user = RoomModel.query.filter_by(room_name = session.get("room")).all()
            message = MessageModel.query.filter_by(room = session.get("room")).all()
            db.session.delete(user[0])
            for i in range(0, len(message)):
                db.session.delete(message[i])
            db.session.commit()

            username = RoomModel.query.filter_by(username=current_user.username).all()
            roomNames = ["a"] * len(username)

            for i in range(0, len(username)):
                roomNames[i] = username[i].room_name

            session["room"] = None

            return redirect("/chat")
        else:
            return render_template('message.html')

@app.route('/login', methods = ['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect('/chat')
     
    if request.method == 'POST':
        username = request.form['username']
        user = UserModel.query.filter_by(username = username).first()
        if user is not None and user.check_password(request.form['password']):
            login_user(user)
            return redirect('/chat')
        elif user is None or not user.check_password(request.form['password']):
            return render_template("login.html", context='Incorrect username or password')
        else:
            return render_template("login.html", context='Incorrect username or password')
    else:
        return render_template('login.html')
 
@app.route('/register', methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect('/chat')
     
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']

        if confirm != password:
            return render_template("register.html", context="Confirmation and password must be the same")
        elif len(password) < 6:
            return render_template("register.html", context="Password must be at least 6 characters")
 
        elif UserModel.query.filter_by(username=username).first():
            return render_template("register.html", context="This username is already in use")
             
        user = UserModel(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')
 
 
@app.route('/logout')
def logout():
    logout_user()
    return redirect('/chat')


if __name__== "__main__":
    socketio.run(app, debug=True)