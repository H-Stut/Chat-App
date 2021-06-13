from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager
 
login = LoginManager()
db = SQLAlchemy()

class MessageModel(UserMixin, db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100))
    content = db.Column(db.String())
    room = db.Column(db.String())
    time = db.Column(db.String())
        

class RoomModel(UserMixin, db.Model):
    __tablename__ = "rooms"

    room_password = db.Column(db.String())
    room_name = db.Column(db.String(100))
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))

    def set_room_password(self, password):
        self.room_password = generate_password_hash(password)

    def check_room_password(self, password):
        return check_password_hash(self.room_password, password)

class UserModel(UserMixin, db.Model):
    __tablename__ = 'users'
 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password_hash = db.Column(db.String()) 
    
    def set_password(self,password):
        self.password_hash = generate_password_hash(password)
     
    def check_password(self,password):
        return check_password_hash(self.password_hash,password)
 
 
@login.user_loader
def load_user(id):
    return UserModel.query.get(int(id))