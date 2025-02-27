from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Инициализация приложения и базы данных
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contacts.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)

# Модели
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Street(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    houses = db.relationship('House', backref='street', lazy=True)

class House(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    house_number = db.Column(db.String(10), nullable=False)
    street_id = db.Column(db.Integer, db.ForeignKey('street.id'), nullable=False)
    contacts = db.relationship('Contact', backref='house', lazy=True)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    house_id = db.Column(db.Integer, db.ForeignKey('house.id'), nullable=False)

# Инициализация login_manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Создание базы данных и администратора
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin")
        admin.set_password("admin_password")  # Создаём пароль для администратора
        db.session.add(admin)
        db.session.commit()

@app.route('/delete_contact/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_contact(id):
    contact = Contact.query.get(id)
    if contact:
        db.session.delete(contact)
        db.session.commit()
        flash('Контакт удалён', 'success')
    else:
        flash('Контакт не найден', 'danger')
    return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
@app.route('/')
def index():
    streets = Street.query.all()  # Получаем все улицы
    return render_template('index.html', streets=streets)

@app.route('/<street_id>')
def show_street(street_id):
    street = Street.query.get_or_404(street_id)
    houses = street.houses  # Получаем все дома на улице
    return render_template('street.html', street=street, houses=houses)

@app.route('/<street_id>/<house_id>')
def show_house(street_id, house_id):
    house = House.query.get_or_404(house_id)
    contacts = house.contacts  # Получаем все контакты для дома
    return render_template('house.html', house=house, contacts=contacts)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_contact():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        house_number = request.form.get('house_number')  # Получаем номер дома
        new_contact = Contact(name=name, phone=phone, address=address, house_number=house_number)
        db.session.add(new_contact)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_contact.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)


#git add .  # Добавляем все изменения
#git commit -m "Обновил код: исправил логин"
#git push origin main  # Отправляем на сервер