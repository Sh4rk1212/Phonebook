from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)  # Было `password`, стало `password_hash`

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)  # Используем более читаемое название
    address = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<Contact {self.name}>'

# Для улучшения производительности можно добавить индексы на поля:
# db.Index('idx_username', User.username)
# db.Index('idx_name', Contact.name)
