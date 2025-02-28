from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contacts.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)

# --- МОДЕЛИ ---
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
    houses = db.relationship('House', backref='street', lazy=True, cascade="all, delete")

class House(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    house_number = db.Column(db.String(10), nullable=False)
    street_id = db.Column(db.Integer, db.ForeignKey('street.id'), nullable=False)
    contacts = db.relationship('Contact', backref='house', lazy=True, cascade="all, delete")

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    house_id = db.Column(db.Integer, db.ForeignKey('house.id'), nullable=False)

# --- НАСТРОЙКА LOGIN_MANAGER ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ГЛАВНАЯ + ПОИСК ---
@app.route('/', methods=['GET', 'POST'])
def index():
    streets = Street.query.all()
    contacts = []
    if request.method == 'POST':
        search_query = request.form.get('search_query', '').strip()
        if search_query:
            contacts = Contact.query.filter(
                (Contact.name.ilike(f"%{search_query}%")) |
                (Contact.address.ilike(f"%{search_query}%"))
            ).all()
    return render_template('index.html', streets=streets, contacts=contacts)


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()

    if not query:
        flash("Введите имя или адрес для поиска!", "warning")
        return redirect(url_for('index'))

    # Поиск по имени или адресу
    results = Contact.query.filter(
        (Contact.name.ilike(f"%{query}%")) | (Contact.address.ilike(f"%{query}%"))
    ).all()

    return render_template('search_results.html', query=query, results=results)


# --- ПРОСМОТР УЛИЦЫ ---
@app.route('/<street_id>')
def show_street(street_id):
    street = Street.query.get_or_404(street_id)
    houses = House.query.filter_by(street_id=street_id).order_by(House.house_number.asc()).all()
    return render_template('street.html', street=street, houses=houses)

# --- ПРОСМОТР ДОМА ---
@app.route('/<street_id>/<house_id>')
def show_house(street_id, house_id):
    house = House.query.get_or_404(house_id)
    contacts = house.contacts
    return render_template('house.html', house=house, contacts=contacts)

# --- ДОБАВЛЕНИЕ УЛИЦЫ ---
@app.route('/add_street', methods=['GET', 'POST'])
@login_required
def add_street():
    if request.method == 'POST':
        street_name = request.form['street_name']
        if not Street.query.filter_by(name=street_name).first():
            new_street = Street(name=street_name)
            db.session.add(new_street)
            db.session.commit()
            flash('Улица добавлена', 'success')
        else:
            flash('Такая улица уже существует', 'danger')
        return redirect(url_for('index'))
    return render_template('add_street.html')

# --- УДАЛЕНИЕ УЛИЦЫ ---
@app.route('/delete_street/<int:street_id>', methods=['POST'])
@login_required
def delete_street(street_id):
    street = Street.query.get_or_404(street_id)
    db.session.delete(street)
    db.session.commit()
    flash('Улица удалена', 'success')
    return redirect(url_for('index'))

# --- ДОБАВЛЕНИЕ ДОМА ---
@app.route('/add_house/<street_id>', methods=['GET', 'POST'])
@login_required
def add_house(street_id):
    street = Street.query.get_or_404(street_id)
    if request.method == 'POST':
        house_number = request.form['house_number']
        if not House.query.filter_by(house_number=house_number, street_id=street.id).first():
            new_house = House(house_number=house_number, street_id=street.id)
            db.session.add(new_house)
            db.session.commit()
            flash('Дом добавлен', 'success')
        else:
            flash('Такой дом уже существует', 'danger')
        return redirect(url_for('show_street', street_id=street.id))
    return render_template('add_house.html', street=street)

# --- УДАЛЕНИЕ ДОМА ---
@app.route('/delete_house/<int:house_id>', methods=['POST'])
@login_required
def delete_house(house_id):
    house = House.query.get_or_404(house_id)
    street_id = house.street_id
    db.session.delete(house)
    db.session.commit()
    flash('Дом удалён', 'success')
    return redirect(url_for('show_street', street_id=street_id))

# --- ДОБАВЛЕНИЕ КОНТАКТА ---
@app.route('/add_contact_to_house/<int:house_id>', methods=['GET', 'POST'])
@login_required
def add_contact_to_house(house_id):
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        if not address:
            flash("Ошибка: Адрес обязателен!", "danger")
            return redirect(url_for('add_contact_to_house', house_id=house_id))
        new_contact = Contact(name=name, phone=phone, address=address, house_id=house_id)
        db.session.add(new_contact)
        db.session.commit()
        flash('Контакт добавлен', 'success')
        return redirect(url_for('index'))
    return render_template('add_contact_to_house.html', house_id=house_id)

# --- УДАЛЕНИЕ КОНТАКТА ---
@app.route('/delete_contact/<int:contact_id>', methods=['POST'])
@login_required
def delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)  # Проверяем, есть ли контакт
    db.session.delete(contact)
    db.session.commit()
    flash('Контакт удалён', 'success')

    return redirect(url_for('index'))


# --- АВТОРИЗАЦИЯ ---
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
            flash('Неверный логин или пароль', 'danger')

    return render_template('login.html')

# --- ВЫХОД ИЗ АККАУНТА ---
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