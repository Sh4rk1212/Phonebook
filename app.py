from flask import Flask, render_template, request, redirect, url_for
from database import db, Contact

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contacts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "supersecretkey"

db.init_app(app)

# Создаём таблицы перед первым запросом
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    contacts = Contact.query.all()
    return render_template('index.html', contacts=contacts)

@app.route('/add', methods=['GET', 'POST'])
def add_contact():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']  # Получаем адрес
        new_contact = Contact(name=name, phone=phone, address=address)
        db.session.add(new_contact)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_contact.html')

@app.route('/search')
def search():
    query = request.args.get('query')
    if query:
        contacts = Contact.query.filter(
            (Contact.name.ilike(f"%{query}%")) |
            (Contact.phone.ilike(f"%{query}%")) |
            (Contact.address.ilike(f"%{query}%"))
        ).all()
    else:
        contacts = Contact.query.all()
    return render_template('index.html', contacts=contacts)


@app.route('/delete/<int:id>')
def delete_contact(id):
    contact = Contact.query.get(id)
    if contact:
        db.session.delete(contact)
        db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
