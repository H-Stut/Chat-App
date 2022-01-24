from argparse import Namespace
from datetime import datetime
from math import ceil, log
import math
from re import A
from flask import Flask, session, request, redirect
from flask.templating import render_template
from flask_login import login_required, current_user, login_user, logout_user
from flask_socketio import SocketIO, join_room, leave_room
from numpy import broadcast
from models import MessageModel, RoomModel, db, login, BanModel, UserModel, ConnectedUsers
app = Flask(__name__)

app.secret_key = 'secret'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SECRET_TYPE"] = "secret"
app.config["SESSION_TYPE"] = "filesystem"

db.init_app(app)
login.init_app(app)
login.login_view = 'login'
socketio = SocketIO(app)
quantity = 20

@app.before_first_request
def create_all():
    db.create_all()

@app.route("/")
def root():
    return redirect("/chat")
def scanUsername(list, term):
    for item in list:
        if term == item.username:
            return item
    return None
clients = []
@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    if request.method == "POST":
        if "join" in request.form:
            room = request.form["name"]

            roomNames = getRooms()

            bans = BanModel.query.filter_by(room=room).all()
            if scanUsername(bans, current_user.username) != None:
                return render_template("chat.html", rooms=roomNames, context="You are banned from this room!")
            
            password = request.form["password"]
            name = RoomModel.query.filter_by(room_name=room).first()
            if name is not None and name.check_room_password(password):
                session["room"] = room
                session["username"] = current_user.username
                return redirect("/message")
            elif name is None:
                return render_template("chat.html", context=f"Room {room} does not exist!", rooms=roomNames)
            elif not name.check_room_password(password):
                return render_template("chat.html", context="Incorrect room name or password", rooms=roomNames)
            return render_template("chat.html")
        elif "create" in request.form:
            roomNames = getRooms()
            password = request.form["password"]
            room = request.form["name"]

            if len(room) > 32:
                return render_template("chat.html", context="Room name cannot be longer that 32 characters",rooms=roomNames)
            elif len(password) > 64:
                return render_template("chat.html", context="Password cannot be longer that 64 characters",rooms=roomNames)
            elif len(room) < 6:
                return render_template("chat.html", context="Room name must be longer that 6 characters", rooms=roomNames)
            
            name = RoomModel.query.filter_by(room_name=room).first()
            if name is not None:
                return render_template("chat.html", context="Room name already exists did you mean to join?", rooms=roomNames)
            else:
                session["room"] = room
                session["username"] = current_user.username
                username = RoomModel.query.filter_by(username=current_user.username).all()
                if len(username) > 20:
                    return render_template("chat.html", context="You cannot create more than 20 chat rooms per account", rooms=roomNames)
                user = RoomModel()
                user.room_name = room
                user.username = current_user.username
                user.set_room_password(password)
                db.session.add(user)
                db.session.commit()
                return redirect("/message")
        elif "joinS" in request.form:
            room = request.form["joinS"]
            room_to_join = RoomModel.query.filter_by(room_name=room).first()
            if room_to_join == None:
                return redirect("/chat")
                
            owner = room_to_join.username
            if current_user.username != owner:
                return redirect("/chat")

            session["room"] = room
            session["username"] = current_user.username
            return redirect("/message")
        return render_template("chat.html")
    else:
        roomNames = getRooms()
        return render_template("chat.html", rooms=roomNames)

@socketio.on("kick")
def kick(data):
    user = RoomModel.query.filter_by(room_name=session["room"]).first()
    if current_user.username != user.username:
        return

    username = data["username"]
    user_to_kick = UserModel.query.filter_by(username=username).first()


    socketio.emit("user leave", {
        "user" :user_to_kick.username
    }, callback=leaveRoom, room=session["room"])

    user_to_kick.room = None
    db.session.add(user_to_kick)
    db.session.commit()
    leave_room(room=session["room"], sid=user_to_kick.sid)
    socketio.emit("redirect",{
        "url" : "/chat",
        "alert": False,
        "text" : ""
    }, callback=kick, room=user_to_kick.sid)
    connected = ConnectedUsers.query.filter_by(username=user_to_kick.username).first()
    if (connected):
        db.session.delete(connected)
        db.session.commit()

@app.route("/profile")
@login_required
def prof():
    return render_template("profile.html", username=current_user.username)

@socketio.on("setImage")
def setImage(data):
    photoData = data["data"]
    photo = UserModel.query.filter_by(username=current_user.username).first()

    photo.image = photoData
    db.session.add(photo)
    db.session.commit()

@socketio.on("profile")
def getProfile():
    messages = MessageModel.query.filter_by(author=current_user.username).all()
    pfp = UserModel.query.filter_by(username=current_user.username).first()
    message_len = len(messages)
    if (pfp.image == None):
        socketio.emit("getProfileData",{
            "totalMess" : message_len
        }, callback=getProfile, room=request.sid)
        return
    socketio.emit("getProfileData",{
        "totalMess" : message_len,
        "pfp" : pfp.image
    }, callback=getProfile, room=request.sid)

@socketio.on("unban")
def unban(data):
    user = RoomModel.query.filter_by(room_name=session["room"]).first()
    bans = BanModel.query.filter_by(room=session["room"]).all()

    if (current_user.username != user.username):
        return
    
    for ban in bans:
        if data["username"] == ban.username:
            db.session.delete(ban)
            db.session.commit()
    socketio.emit("unbanned",{
        "user" : data["username"]
    }, callback=unban, room=request.sid)

@socketio.on("ban")
def ban(data):
    user = RoomModel.query.filter_by(room_name=session["room"]).first()
    username = data["username"]

    if current_user.username != user.username:
        return
    connected = ConnectedUsers.query.filter_by(username=username).first()
    if (connected):
        db.session.delete(connected)
        db.session.commit()

    ban = BanModel()
    ban.username = username
    ban.room = session["room"]
    db.session.add(ban)
    db.session.commit()

    user_to_kick = UserModel.query.filter_by(username=username).first()
    messages = MessageModel.query.filter_by(author=username).all()
    ids = []
    for message in messages:
        if message.room == session["room"]:
            ids.append(message.id)
            db.session.delete(message)
            db.session.commit()
    
    socketio.emit("user leave", {
        "user" : user_to_kick.username
    }, callback=leaveRoom, room=session["room"])
    socketio.emit("user ban", {
        "user" : user_to_kick.username
    }, callback=leave_room, room=request.sid)
    socketio.emit("message deleted", {
        "large" : True,
        "id" : ids
    }, callback=delelteMessage, room=session["room"])

    socketio.emit("redirect", {
        "url" :"/chat",
        "alert" : True,
        "text" : "You have been banned from the room, "
    }, callback=kick, room=user_to_kick.sid)

    leave_room(room=session["room"], sid=user_to_kick.sid)
    user_to_kick.room = None
    db.session.add(user_to_kick)
    db.session.commit()

@socketio.on("remove")
def removeRoom():
    wipe_room()
    user = RoomModel.query.filter_by(room_name = session["room"]).first()
    message = MessageModel.query.filter_by(room = session["room"]).all()
    bans = BanModel.query.filter_by(room=session["room"]).all()
    connected = ConnectedUsers.query.filter_by(room=session["room"]).first()
    if (connected):
        db.session.delete(connected)
        db.session.commit()

    if current_user.username != user.username:
        return

    for ban in bans:
        db.session.delete(ban)
        db.session.commit()

    db.session.delete(user)
    for i in range(0, len(message)):
        db.session.delete(message[i])
    db.session.commit()

    socketio.emit("redirect", {
        "url" : "/chat",
        "alert" : True,
        "text" : "The host has deleted the room, "
        }, callback=removeRoom, room=session["room"])
    leave_room(session["room"])
    session["room"] = None

@socketio.on("leave")
def leaveRoom():
    connected = ConnectedUsers.query.filter_by(username=current_user.username).first()
    if (connected):
        db.session.delete(connected)
        db.session.commit()
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
wiped_room = {}
def wipe_room():
    wiped_room[session["room"]] = True
    users = ConnectedUsers.query.filter_by(room=session["room"]).all()
    for user in users:
        db.session.delete(user)
    db.session.commit()

def add_and_checkUser():
    found = False
    exists = ConnectedUsers.query.filter_by(username=current_user.username).first()
    if (not exists):
        connected_users = ConnectedUsers()
        connected_users.username = current_user.username
        connected_users.room = session["room"]
        db.session.add(connected_users)
        db.session.commit()
        found = True
    return found

@socketio.on("connected")
def connected():
    banList = getAndCheckBans(True)
    found = add_and_checkUser()

    join_room(session["room"])
    checkAndWipeRoom()

    socketio.emit("check status", callback=connected, room=session["room"])
    owner = getRoomOwner()

    allMessages = MessageModel.query.filter_by(room=session["room"]).all()
    message_data = getMessagesInvert(allMessages, 0)

    old_user = UserModel.query.filter_by(username=current_user.username).first()
    new_user = old_user
    new_user.room = session["room"]
    new_user.sid = request.sid
    editDB(old_user, new_user)

    users = getConnectedUsers()
    json_message_data = getMessageDataDict(message_data)
    socketio.emit("get",{
        "message_data" : json_message_data,
        "username" : current_user.username,
        "owner" : owner,
        "users" : users,
        "bans" : banList
    }, callback=connected, room=request.sid)
    if (found):
        socketio.emit("user join", {
            "user" : current_user.username
        }, callback=connected, room=session["room"])
@socketio.on("socket active")
def socket_active():
    found = add_and_checkUser()
@socketio.on("get messages")
def socketGetMessages(json):
    counter = json["counter"]
    allMessages = MessageModel.query.filter_by(room=session["room"]).all()
    message_data = getMessagesInvert(allMessages, counter)
    
    finished = False
    json_message_data = []
    if not message_data:
        finished = True
    else: json_message_data = getMessageDataDict(message_data)

    socketio.emit("appendMess",{
        "messages" : json_message_data,
        "finished" : finished
    }, callback=socketGetMessages, room=request.sid)

@socketio.on("get pfp")
def getPFP(json):
    users = json["users"]
    pfps = [""] * len(users)
    for i in range(len(users)):
        user = users[i]
        users2 = UserModel.query.filter_by(username=user).first()
        messages = MessageModel.query.filter_by(room=session["room"]).all()
        user_to_get = ConnectedUsers.query.filter_by(username=user).first()
        for message in messages:
            if (message.author == user):
                if (users2.image):
                    pfps[i] = users2.image
                    break
        if (user_to_get):
            if (users2.image and user_to_get.room == session["room"]):
                pfps[i] = users2.image
    socketio.emit("pfps",{
        "pfps" : pfps
    }, callback=getPFP, room=request.sid)

def getConnectedUsers():
    connected_clients = ConnectedUsers.query.filter_by(room=session["room"]).all()
    users = []
    for client in connected_clients:
        users.append(client.username)
    return users

def getRoomOwner():
    room = RoomModel.query.filter_by(room_name=session["room"]).first()
    owner = room.username
    return owner

def editDB(old, new):
    db.session.delete(old)
    db.session.add(new)
    db.session.commit()

def checkAndWipeRoom():
    if session["room"] in wiped_room:
        if not wiped_room[session["room"]]:
            wipe_room()
    else:
        wipe_room()

def getAndCheckBans(check):
    banList = []
    owner = getRoomOwner()
    bans = BanModel.query.filter_by(room=session["room"]).all()

    if check:
        for ban in bans:
            if ban.username == current_user.username:
                socketio.emit("redirect", {
                    "url" : "/chat",
                    "alert" : False,
                    "text" : ""
                }, callback=connected, room=request.sid)

    if (current_user.username == owner):
        for ban in bans:
            banList.append(ban.username)
    return banList

@socketio.on("message sent")
def messageReceived(json):
    messages = MessageModel()
    messages.room = session["room"]
    messages.author = current_user.username
    messages.content = json["message"]

    if len(messages.content) == 0:
        return
    now = datetime.now().timestamp()
    messages.time = now

    db.session.add(messages)
    db.session.commit()

    json_message_data = getMessageDataDict([messages])

    socketio.emit("get",{
        "message_data" : json_message_data,
        "username" : current_user.username,
        "owner" : getRoomOwner(),
        "bans" : getAndCheckBans(False),
        "users" : getConnectedUsers()
    }, room=session["room"], callback=messageReceived)

def getMessagesInvert(messages, count):
    selector = math.floor((count + quantity) / quantity)
    extra = (count + quantity) % quantity
    if (len(messages) <= count): return
    startpoint = len(messages) - (selector*quantity)
    startpoint -= extra
    if (selector*quantity + extra> len(messages)): startpoint = 0
    endpoint = len(messages) - ((selector -1)*quantity)
    endpoint -= extra
    return messages[startpoint:endpoint]

def getMessageDataDict(message_data):
    if (not message_data): return
    json_message_data = []
    for message in message_data:
        message_dict = {}
        message_dict["author"] = message.author
        message_dict["id"] = message.id
        message_dict["content"] = message.content
        message_dict["time"] = message.time

        json_message_data.append(message_dict)
    return json_message_data
@app.route("/message", methods=["POST", "GET"])
@login_required
def message():
    if request.method == "GET":
        if session["room"] == None:
            return redirect("/chat")

        username = current_user.username
        room = session["room"]
        room2 = RoomModel.query.filter_by(room_name=room).first()
        if room2 == None:
            return redirect("/chat")
        owner = room2.username
        if username == owner:
            return render_template("message.html", session=session, admin=True)
        return render_template("message.html", session=session, admin=False)
    else:
        if "leave" in request.form:
            session["room"] == None
            connected = ConnectedUsers.query.filter_by(username=current_user.username).first()
            if (connected):
                db.session.delete(connected)
                db.session.commit()
            return redirect("/chat")
        else:
            return render_template("message.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        user = UserModel.query.filter_by(username=username).first()
        if user is None:
            return render_template("login.html", context="User does not exist!")
        elif user.check_password(request.form["password"]):
            login_user(user)
            return redirect("/chat")
        else:
            return render_template("login.html", context="Username or password is incorrect!")
    else:
        return render_template("login.html")

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
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

@app.route("/logout")
def logout():
    logout_user()
    return redirect("/chat")

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
def getRooms():
    username = RoomModel.query.filter_by(username=current_user.username).all()
    roomNames = [username[i].room_name for i in range(len(username))]
    return roomNames

if __name__=="__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=80)