import re
from flask import Flask,render_template,request,redirect, session
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug import debug
from models import BanModel, RoomModel, UserModel,db,login, MessageModel, ImageModel
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_session import Session
from datetime import datetime
import math
 
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

@app.route("/")
def root():
    return redirect("/chat")


@app.route('/chat', methods=["GET", "POST"])
@login_required
def chat():
    if request.method=="POST":
        if "join" in request.form:
            room = request.form["name"]
            username = RoomModel.query.filter_by(username=current_user.username).all()
            roomNames = ["a"] * len(username)
            for i in range(0, len(username)):
                roomNames[i] = username[i].room_name

            bans = BanModel.query.filter_by(room=room).all()
            for i in range(0, len(bans)):
                if(bans[i].username == current_user.username):
                    return render_template("chat.html", rooms=roomNames, context="You are banned from this room!")               
            password = request.form["password"]
            session["room"] = room
            session["username"] = current_user.username

            name = RoomModel.query.filter_by(room_name=room).first()
            if name is not None and name.check_room_password(password):
                return redirect("/message")
            elif name is None:
                return render_template("chat.html", context="Room does not exist", rooms=roomNames)
            elif name is None or not name.check_room_password(password):
                return render_template("chat.html", context="Incorrect room name or password", rooms=roomNames)
            return render_template("chat.html")
        elif "create" in request.form:
            username = RoomModel.query.filter_by(username=current_user.username).all()
            roomNames = ["a"] * len(username)
            password = request.form["password"]

            for i in range(0, len(username)):
                roomNames[i] = username[i].room_name

            room = request.form["name"]
            if len(room) > 32:
                return render_template("chat.html", context="Room name cannot be longer that 32 characters",rooms=roomNames)
            elif len(password) > 64:
                return render_template("chat.html", context="Password cannot be longer that 64 characters",rooms=roomNames)
            elif len(room) < 6:
                return render_template("chat.html", context="Room name must be longer that 6 characters", rooms=roomNames)

            session["room"] = room
            session["username"] = current_user.username



            name = RoomModel.query.filter_by(room_name=room).first()
            if name is not None:
                return render_template("chat.html", context="Room name already exists did you mean to join?",  session=session, count=len(username), rooms=roomNames)
            if name is None:
                username = RoomModel.query.filter_by(username=current_user.username).all()
                if len(username) > 20:
                    return render_template("chat.html", context="You cannot create more than 20 chat rooms per account", session=session, count=len(username), rooms=roomNames)
                user = RoomModel()
                user.room_name = room
                user.username = current_user.username
                user.set_room_password(password)
                db.session.add(user)
                db.session.commit()
                return redirect("/message")
        elif "joinS" in request.form:
            room = request.form["joinS"]
            room2 = RoomModel.query.filter_by(room_name=room).first()
            if room2 == None:
                username = RoomModel.query.filter_by(username=current_user.username).all()
                roomNames = ["a"] * len(username)
                for i in range(0, len(username)):
                    roomNames[i] = username[i].room_name
                return redirect("/chat")

            owner = room2.username
            if (current_user.username != owner):
                return redirect("/chat")
            session["room"] = room
            return redirect("/message")
        return render_template("chat.html", session=session)
    else:
        username = RoomModel.query.filter_by(username=current_user.username).all()
        roomNames = ["a"] * len(username)
        for i in range(0, len(username)):
            roomNames[i] = username[i].room_name
        return render_template('chat.html', session=session, count=len(username), rooms=roomNames)

@socketio.on("kick")
def kick(json):
    user = RoomModel.query.filter_by(room_name = session.get("room")).first()
    if current_user.username != user.username:
        return
    username = json["username"]
    usertokick = UserModel.query.filter_by(username=username).first()
    socketio.emit("user leave", {
        "user" : usertokick.username
    }, callback=leaveRoom, room=session["room"])
    usertokick.room = ""
    db.session.add(usertokick)
    db.session.commit()
    leave_room(room=session["room"], sid=usertokick.sid)
    socketio.emit("redirect", {
        "url" :"/chat",
        "alert" : False,
        "text" : ""
    }, callback=kick, room=usertokick.sid)

@app.route("/profile")
@login_required
def prof():
    return render_template("profile.html", username=current_user.username)

@socketio.on("setImage")
def setImage(json):
    data = json["data"]
    photos = ImageModel.query.filter_by(username=current_user.username).all()
    if (len(photos) != 0):
        photos[0].image = data
        photos[0].username=current_user.username
        db.session.add(photos[0])
        db.session.commit()
    else:
        pics = ImageModel(username=current_user.username)
        pics.image = data
        db.session.add(pics)
        db.session.commit()

@socketio.on("profile")
def profile():
    messages = MessageModel.query.filter_by(author=current_user.username).all()
    pfp = ImageModel.query.filter_by(username=current_user.username).first()
    MessageLen = len(messages)
    if (pfp == None):
        socketio.emit("getProfileData", {
            "totalMess" : MessageLen
        }, callback=profile, room=request.sid)
    else:
        socketio.emit("getProfileData", {
            "totalMess" : MessageLen,
            "pfp" : pfp.image
        }, callback=profile, room=request.sid)

@socketio.on("unban")
def unban(json):
    user = RoomModel.query.filter_by(room_name = session.get("room")).first()
    bans = BanModel.query.filter_by(room=session.get("room")).all()

    if current_user.username != user.username:
        return

    for ban in bans:
        if (json["username"] == ban.username):
            db.session.delete(ban)
            db.session.commit()
    
    socketio.emit("unbanned", {
        "user" : json["username"]
    }, callback=unban, room=request.sid)

@socketio.on("ban")
def ban(json):
    user = RoomModel.query.filter_by(room_name = session.get("room")).first()
    username = json["username"]
    userRooms = UserModel.query.filter_by(room=session.get("room")).all()
    found = False
    if current_user.username != user.username:
        return

    ban = BanModel()
    ban.username = username
    ban.room = session["room"]
    db.session.add(ban)
    db.session.commit()

    usertokick = UserModel.query.filter_by(username=username).first()
    messages = MessageModel.query.filter_by(author=username).all()
    ids = []
    for message in messages:
        if message.room == session.get("room"):
            ids.append(message.id)
            db.session.delete(message)
            db.session.commit()
    socketio.emit("user leave", {
        "user" : usertokick.username
    }, callback=leaveRoom, room=session["room"])
    socketio.emit("user ban", {
        "user" : usertokick.username
    }, callback=leave_room, room=request.sid)
    socketio.emit("message deleted", {
        "large" : True,
        "id" : ids
    }, callback=delelteMessage, room=session["room"])
    
    socketio.emit("redirect", {
        "url" :"/chat",
        "alert" : True,
        "text" : "You have been banned from the room, "
    }, callback=kick, room=usertokick.sid)

    leave_room(room=session["room"], sid=usertokick.sid)

    usertokick.room = ""
    db.session.add(usertokick)
    db.session.commit()

@socketio.on("remove")
def removeRoom():
    user = RoomModel.query.filter_by(room_name = session.get("room")).first()
    message = MessageModel.query.filter_by(room = session.get("room")).all()
    bans = BanModel.query.filter_by(room=session.get("room")).all()

    if current_user.username != user.username:
        return

    for ban in bans:
        db.session.delete(ban)
        db.session.commit()

    db.session.delete(user)
    for i in range(0, len(message)):
        db.session.delete(message[i])
    db.session.commit()

    username = RoomModel.query.filter_by(username=current_user.username).all()
    roomNames = ["a"] * len(username)
    for i in range(0, len(username)):
        roomNames[i] = username[i].room_name

    socketio.emit("redirect", {
        "url" : "/chat",
        "alert" : True,
        "text" : "The host has deleted the room, "
        }, callback=removeRoom, room=session.get("room"))

    leave_room(session.get("room"))
    session["room"] = None
@socketio.on("leave")
def leaveRoom():
    test = UserModel.query.filter_by(username=current_user.username).first()
    usermondel = UserModel.query.filter_by(username=current_user.username).first()
    usermondel.room = None
    socketio.emit("redirect", {
        "url" : "/chat",
        "alert" : False
    }, callback=leaveRoom, room=request.sid)
    socketio.emit("user leave", {
        "user" : current_user.username
    }, callback=leaveRoom, room=session["room"])

    leave_room(session.get("room"))
    session["room"] = None
    db.session.delete(test)
    db.session.add(usermondel)
    db.session.commit()

@socketio.on("edit message")
def edit(json):
    id = json["id"]
    text = json["text"]
    if (len(text) == 0):
        return
    messages = MessageModel.query.filter_by(id=id).first()
    Rooms = RoomModel.query.filter_by(room_name=session["room"]).first()
    if (current_user.username != messages.author):
        return
    db.session.delete(messages)
    messages.content = text
    db.session.add(messages)
    db.session.commit()

    socketio.emit("message edited", {
        "text" : text,
        "id" : id
    }, callback=edit, room=session["room"])

@socketio.on("load")
def load(json):
    Userss = UserModel.query.filter_by(room=session["room"]).all()
    allMessages = MessageModel.query.filter_by(room=session.get("room")).all()
    allRooms = RoomModel.query.filter_by(room_name=session.get("room")).all()
    owner = allRooms[0].username

    section_to_load = json["section"] +1
    base_length = 26

    length_of_section = len(allMessages) % base_length
    number_of_sections = math.ceil(len(allMessages) / base_length)

    section_to_load = number_of_sections - section_to_load

    if length_of_section == 0:
        length_of_section = base_length
    
    section_start = (base_length * section_to_load) - (base_length - length_of_section)
    section_end = section_start + base_length

    if (section_to_load == 0):
        base_length = length_of_section
        section_start = 0
        section_end = length_of_section

    content=[""] * base_length
    authors=[""] * base_length
    time=[0] * base_length
    times=[""] * base_length
    ids=[""] * base_length

    timezone = json["timezone"]
    
    j = 0
    if (section_start < 0):
        return
    for i in range(section_start, section_end):
        content[j] = allMessages[i].content
        authors[j] = allMessages[i].author
        time[j] = int(allMessages[i].time) /60
        times[j] = datetime.utcfromtimestamp((time[j] + timezone *-1) * 60)
        time[j] = times[j].strftime("%d %b %Y %I:%M %p")
        ids[j] = allMessages[i].id
        j+=1

    userarr = ["a"] * len(Userss)

    for i in range(0, len(Userss)):
        userarr[i] = Userss[i].username

    userarr = ["a"] * len(Userss)
    socketio.emit('loadNew', {
        "author" : authors,
        "content" : content,
        "time" : time,
        "username" : current_user.username,
        "session" : session.get("room"),
        "owner" : owner,
        "users" : userarr,
        "ids" : ids,
        "len" : number_of_sections
        }, callback=messageReceived, room=request.sid)

@socketio.on("connected")
def connected(json, methods=["GET", "POST"]):
    User = UserModel.query.filter_by(username=current_user.username).first()
    Userss = UserModel.query.filter_by(room=session["room"]).all()
    User.sid = request.sid
    User.room = session["room"]
    db.session.add(User)
    db.session.commit()
    allMessages = MessageModel.query.filter_by(room=session.get("room")).all()
    allRooms = RoomModel.query.filter_by(room_name=session.get("room")).all()
    bans = BanModel.query.filter_by(room=session.get("room")).all()
    for i in range(0, len(bans)):
        if(bans[i].username == current_user.username):
            socketio.emit("redirect", {
            "url" : "/chat",
            "alert" : False,
            "text" : "The host has deleted the room, "
            }, callback=removeRoom, room=request.sid)
        
    join_room(session.get("room"))
    owner = allRooms[0].username

    base_length = 26

    if len(allMessages) < base_length:
        length = len(allMessages)
    else:
        length = base_length
    content=[""] * length
    authors=[""] * length
    time=[0] * length
    times=[""] * length
    ids=[""] * length

    timezone = json["timezone"]
    section = json["section"]

    secLen = len(allMessages) - (base_length * (section +1))
    secLen2 = len(allMessages) - (base_length * section)

    if len(allMessages) < base_length:
        secLen = 0
        secLen2 = len(allMessages)
    j = 0

    for i in range(secLen, secLen2):
        content[j] = allMessages[i].content
        authors[j] = allMessages[i].author
        time[j] = int(allMessages[i].time) /60
        times[j] = datetime.utcfromtimestamp((time[j] + timezone *-1) * 60)
        time[j] = times[j].strftime("%d %b %Y %I:%M %p")
        ids[j] = allMessages[i].id
        j+=1

    userarr = ["a"] * len(Userss)
    banList = []
    if (current_user.username == owner):
        for ban in bans:
            banList.append(ban.username)

    for i in range(0, len(Userss)):
        userarr[i] = Userss[i].username

    socketio.emit('get', {
        "author" : authors,
        "content" : content,
        "time" : time,
        "username" : current_user.username,
        "session" : session.get("room"),
        "owner" : owner,
        "users" : userarr,
        "ids" : ids,
        "bans" : banList
        }, callback=messageReceived, room=request.sid)

    socketio.emit("user join", {
        "user" : current_user.username
    }, callback=messageReceived, room=session["room"])
@socketio.on("delete message")
def delelteMessage(json):
    id = json["id"]
    messages = MessageModel.query.filter_by(id=id).first()
    Rooms = RoomModel.query.filter_by(room_name=session["room"]).first()
    if (current_user.username != messages.author and Rooms.username != current_user.username):
        return
    db.session.delete(messages)
    db.session.commit()

    socketio.emit("message deleted", {
        "large" : False,
        "id" : id
    }, callback=delelteMessage, room=session["room"])

@socketio.on('message sent')
def messageReceived(json, methods=['GET', 'POST']):
    json["username"] = current_user.username
    timezone = json["timezone"]
    test = datetime.now().timestamp() /60
    
    times = datetime.utcfromtimestamp((test + timezone *-1) * 60)
    time = times.strftime("%d %b %Y %I:%M %p")

    messages = MessageModel()
    messages.room = session.get("room")
    messages.author = current_user.username
    messages.content = json["message"]
    if len(messages.content) == 0:
        return
    now = datetime.now().timestamp()
    messages.time = now

    db.session.add(messages)
    db.session.commit()

    Messages = MessageModel.query.filter_by(room=session.get("room")).all()
    Message = Messages[-1]
    content=Message.content
    authors=Message.author
    id=Message.id

    
    socketio.emit('message recieved', {
        "author" : authors,
        "content" : content,
        "time" : time,
        "username" : current_user.username,
        "session" : session.get("room"),
        "id" : id
        }, room=session.get("room"),callback=messageReceived)

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
        if "leave" in request.form:
            session["room"] = None
            return redirect("/chat")
        else:
            return render_template('message.html')

@app.route('/login', methods = ['POST', 'GET'])
def login():
     
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
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']

        if confirm != password:
            return render_template("register.html", context="Confirmation and password must be the same")
        elif len(password) < 6:
            return render_template("register.html", context="Password must be at least 6 characters")
        elif len(password) > 32:
            return render_template("register.html", context="Password cannot be longer than 32 characters")
        elif len(username) < 4:
            return render_template("register.html", context="Username must be at least 4 characters long")
        elif len(username) > 16:
            return render_template("register.html", context="Username must be less than 16 characters")
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