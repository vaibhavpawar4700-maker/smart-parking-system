from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# ---------------- CONFIG ----------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- DATABASE ----------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))

class ParkingSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20))

class ParkingSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.Integer)
    entry_time = db.Column(db.DateTime)
    exit_time = db.Column(db.DateTime)
    amount = db.Column(db.Integer)

# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return render_template('index.html')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            password=request.form['password']
        )
        db.session.add(user)
        db.session.commit()
        return "Registered ✅"
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(
            username=request.form['username'],
            password=request.form['password']
        ).first()

        if user:
            return "Login Successful ✅"
        else:
            return "Invalid ❌"
    return render_template('login.html')

# Create Slots
@app.route('/create_slots')
def create_slots():
    if ParkingSlot.query.count() == 0:
        for i in range(1, 11):
            db.session.add(ParkingSlot(status="Available"))
        db.session.commit()
        return "Slots Created ✅"
    return "Already Created"

# View Slots
@app.route('/slots')
def slots():
    slots = ParkingSlot.query.all()
    return render_template('slots.html', slots=slots)

# Book Slot
@app.route('/book/<int:id>')
def book(id):
    slot = ParkingSlot.query.get(id)
    if slot.status == "Available":
        slot.status = "Occupied"

        session = ParkingSession(
            slot_id=id,
            entry_time=datetime.now()
        )

        db.session.add(session)
        db.session.commit()

        return "Booked 🚗"
    return "Already Occupied ❌"

# Exit Slot
@app.route('/exit/<int:id>')
def exit(id):
    slot = ParkingSlot.query.get(id)

    session = ParkingSession.query.filter_by(slot_id=id, exit_time=None).first()

    if session:
        session.exit_time = datetime.now()

        duration = (session.exit_time - session.entry_time).seconds // 60

        # Smart Pricing
        hour = datetime.now().hour
        rate = 5 if 18 <= hour <= 22 else 2

        session.amount = duration * rate

        slot.status = "Available"

        db.session.commit()

        return f"Exited 🚪 | ₹{session.amount}"

    return "Error ❌"

# Dashboard
@app.route('/dashboard')
def dashboard():
    total = ParkingSlot.query.count()
    available = ParkingSlot.query.filter_by(status="Available").count()
    occupied = ParkingSlot.query.filter_by(status="Occupied").count()

    return render_template('dashboard.html', total=total, available=available, occupied=occupied)

# History
@app.route('/history')
def history():
    sessions = ParkingSession.query.all()
    return render_template('history.html', sessions=sessions)

# ---------------- MAIN ----------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)