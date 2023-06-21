from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
from test import RideSharingModel, get_route_info

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = '1111'

# Konfiguracja bazy danych SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicjalizacja bazy danych
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Model użytkownika
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    name = db.Column(db.String(80))
    surname = db.Column(db.String(80))
    password = db.Column(db.String(80))

    def __init__(self, email, name, surname, password):
        self.email = email
        self.name = name
        self.surname = surname
        self.password = password


# Model przejazdu
class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    starting_place = db.Column(db.String(100))
    destination = db.Column(db.String(100))
    cost = db.Column(db.Float)
    special_luggage = db.Column(db.Boolean)
    starting_time = db.Column(db.DateTime)

    driver = db.relationship('User', backref=db.backref('driver_rides', lazy=True))

    def __init__(self, driver_id, starting_place, destination, cost, special_luggage, starting_time):
        self.driver_id = driver_id
        self.starting_place = starting_place
        self.destination = destination
        self.cost = cost
        self.special_luggage = special_luggage
        self.starting_time = starting_time

# Strona główna
@app.route('/')
def index():
    return render_template('index1.html')

# Strona główna
@app.route('/drivers')
def drivers():
    return render_template('drivers.html')

@app.route('/drivers', methods=['GET'])
def search_drivers():
    starting_place = request.args.get('startingPlace')
    destination = request.args.get('destination')
    date = request.args.get('date')

    # Konwertuj string daty na obiekt datetime
    search_date = datetime.strptime(date, '%Y-%m-%d')

    # Wybierz przejazdy, których starting_time jest w przedziale 24 godzin od podanej daty
    rides = Ride.query.filter_by(starting_place=starting_place, destination=destination).\
        filter(Ride.starting_time >= search_date, Ride.starting_time < search_date + timedelta(days=1)).all()

    return render_template('drivers.html', rides=rides)


@app.route('/ogloszenie', methods=['GET', 'POST'])
def ogloszenie():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Retrieve the form data
        driver_id = session['user_id']
        starting_place = request.form.get('starting-place')
        destination = request.form.get('destination')
        cost = request.form.get('cost')
        special_luggage = True if request.form.get('special-luggage') else False
        starting_time_str = request.form.get('starting-time')

        # Validate the starting_time_str field
        if not starting_time_str:
            flash('Data i czas rozpoczęcia jest wymagane.')
            return redirect(url_for('ogloszenie'))

        # Convert starting time to datetime object
        starting_time = datetime.strptime(starting_time_str, '%Y-%m-%dT%H:%M')

        # Create a new Ride instance
        new_ride = Ride(
            driver_id=driver_id,
            starting_place=starting_place,
            destination=destination,
            cost=cost,
            special_luggage=special_luggage,
            starting_time=starting_time
        )

        # Add the new ride to the database
        db.session.add(new_ride)
        db.session.commit()

        # Return a response or redirect to a success page
        return render_template('ogloszeniekierowca_success.html')

    return render_template('ogloszeniekierowca.html')

# Strona logowania
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Sprawdzenie poprawności danych logowania
        user = User.query.filter_by(email=email, password=password).first()

        if user:
            # Zalogowano pomyślnie, zapisz informacje o zalogowanym użytkowniku w sesji
            session['user_id'] = user.id
            session['user_email'] = user.email

            # Przekieruj na stronę profilu
            return redirect(url_for('profile'))
        else:
            # Nieprawidłowe dane logowania
            return render_template('login.html', error='Nieprawidłowe dane logowania')

    return render_template('login.html')

# Strona rejestracji
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None  # Inicjalizacja zmiennej przechowującej błędy

    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']

        # Sprawdzenie, czy hasła się zgadzają
        if password != confirm_password:
            error = 'Hasła nie zgadzają się. Spróbuj ponownie.'

        # Sprawdzenie, czy użytkownik już istnieje
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            error = 'Użytkownik o podanym adresie email już istnieje.'

        # Jeżeli wystąpiły błędy, wyświetl formularz z błędami
        if error:
            return render_template('signup.html', error=error)

        # Dodanie nowego użytkownika do bazy danych
        new_user = User(name=name, surname=surname, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        # Pomyślnie zarejestrowano użytkownika, można przekierować na stronę logowania
        return redirect(url_for('login'))

    return render_template('signup.html', error=error)

# Strona profilu użytkownika
@app.route('/profile')
def profile():
    # Sprawdzenie, czy użytkownik jest zalogowany
    if 'user_id' in session:
        # Pobranie danych użytkownika z bazy danych na podstawie ID
        user = User.query.get(session['user_id'])
        # Przekazanie danych użytkownika do szablonu
        return render_template('profile.html', user=user)
    else:
        # Użytkownik nie jest zalogowany, można przekierować na stronę logowania
        return redirect(url_for('login'))

# Wylogowanie użytkownika
@app.route('/logout')
def logout():
    # Usunięcie identyfikatora użytkownika z sesji
    session.pop('user_id', None)
    # Przekierowanie na stronę główną lub inną stronę po wylogowaniu
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Utworzenie tabeli użytkowników w bazie danych, jeśli nie istnieje
    with app.app_context():
        db.create_all()

    app.run(debug=True)
