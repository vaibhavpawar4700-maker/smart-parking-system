from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
import datetime
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- MODELS ----------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))


class Slot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default="Available")


class ParkingSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.Integer)
    entry_time = db.Column(db.DateTime)
    exit_time = db.Column(db.DateTime)
    amount = db.Column(db.Integer)


# ---------------- ROUTES ----------------

@app.route('/')
def index():
    total = Slot.query.count()
    available = Slot.query.filter_by(status="Available").count()
    occupied = Slot.query.filter_by(status="Occupied").count()

    return render_template('index.html',
                           total=total,
                           available=available,
                           occupied=occupied)


# -------- REGISTER --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            password=request.form['password']
        )
        db.session.add(user)
        db.session.commit()

        flash("Registration Successful ✅")
        return redirect('/login')

    return render_template('register.html')


# -------- LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(
            username=request.form['username'],
            password=request.form['password']
        ).first()

        if user:
            session['user'] = user.username
            flash("Login Successful 🔥")
            return redirect('/')
        else:
            flash("Invalid Login ❌")

    return render_template('login.html')


# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out")
    return redirect('/')


# -------- CREATE SLOTS --------
@app.route('/create_slots')
def create_slots():
    if Slot.query.count() == 0:
        for i in range(20):
            db.session.add(Slot())
        db.session.commit()
        flash("Slots Created Successfully 🚗")
    else:
        flash("Slots Already Exist ⚠️")

    return redirect('/')


# -------- VIEW SLOTS --------
@app.route('/slots')
def slots():
    slots = Slot.query.all()
    return render_template('slots.html', slots=slots)


# -------- BOOK SLOT --------
@app.route('/book/<int:id>')
def book(id):
    slot = Slot.query.get(id)

    if slot.status == "Available":
        slot.status = "Occupied"

        session_data = ParkingSession(
            slot_id=id,
            entry_time=datetime.datetime.now()
        )

        db.session.add(session_data)
        db.session.commit()

        flash("Slot Booked 🚗")

    return redirect('/slots')


# -------- EXIT + PAYMENT --------
@app.route('/exit/<int:id>')
def exit(id):
    slot = Slot.query.get(id)
    slot.status = "Available"

    ps = ParkingSession.query.filter_by(slot_id=id, exit_time=None).first()

    if ps:
        ps.exit_time = datetime.datetime.now()

        hours = (ps.exit_time - ps.entry_time).seconds // 3600 + 1
        ps.amount = hours * 20

        db.session.commit()

        flash(f"Payment: ₹{ps.amount}")

    return redirect('/slots')


# -------- HISTORY --------
@app.route('/history')
def history():
    data = ParkingSession.query.all()
    return render_template('history.html', data=data)


# -------- PROFILE --------
@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect('/login')

    return render_template('profile.html', user=session['user'])


# -------- PROJECT INFO --------
@app.route('/project')
def project():
    return render_template('project.html')


# ---------------- MAIN ----------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
