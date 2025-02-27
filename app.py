from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, User, Contact

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contacts.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Перенаправление на страницу входа, если не аутентифицирован

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 📌 Регистрация админа (один раз в консоли)
@app.before_first_request
def create_admin():
    db.create_all()  # Создаём таблицы
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin")
        admin.set_password("admin_password")  # Устанавливаем хэшированный пароль
        db.session.add(admin)
        db.session.commit()

# 🏠 Главная страница (показываем контакты)
@app.route('/')
def index():
    contacts = Contact.query.all()
    return render_template('index.html', contacts=contacts)

# ➕ Добавление контакта (только для админа)
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_contact():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        new_contact = Contact(name=name, phone=phone, address=address)
        new_contact.save()
        return redirect(url_for('index'))
    return render_template('add_contact.html')

# 🔑 Логин
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):  # Проверяем хэш пароля
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль')

    return render_template('login.html')

# 🚪 Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
