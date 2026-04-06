from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import random, smtplib
from twilio.rest import Client

app = Flask(__name__)
app.secret_key = "secret"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mobile = db.Column(db.String(20))
    email = db.Column(db.String(50))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    price = db.Column(db.String(20))
    image = db.Column(db.String(100))

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mobile = db.Column(db.String(20))
    product_name = db.Column(db.String(50))

# OTP Generation
def send_email(email, otp):
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login("your_email@gmail.com", "your_password")
    server.sendmail("your_email@gmail.com", email, f"Your OTP is {otp}")
    server.quit()

@app.route('/')
def login():
    return render_template("login.html")

@app.route('/send_otp', methods=['POST'])
def send_otp():
    mobile = request.form['mobile']
    email = request.form['email']
    otp = str(random.randint(1000,9999))
    session['otp'] = otp
    session['mobile'] = mobile
    send_email(email, otp)
    return render_template("otp.html")

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    user_otp = request.form['otp']
    if user_otp == session['otp']:
        return redirect('/index')
    return "Invalid OTP"

@app.route('/index')
def index():
    products = Product.query.all()
    return render_template("index.html", products=products)

@app.route('/book/<int:id>')
def book(id):
    product = Product.query.get(id)
    booking = Booking(mobile=session['mobile'], product_name=product.name)
    db.session.add(booking)
    db.session.commit()

    # WhatsApp Message
    client = Client("TWILIO_SID", "TWILIO_AUTH")
    client.messages.create(
        from_='whatsapp:+14155238886',
        body=f"You booked {product.name}",
        to=f'whatsapp:+91{session["mobile"]}'
    )
    return "Booking Confirmed!"

@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method == 'POST':
        password = request.form['password']
        if password == "admin123":
            return render_template("admin.html")
        else:
            return "Wrong Password"
    return render_template("admin_login.html")

@app.route('/add_item', methods=['POST'])
def add_item():
    name = request.form['name']
    price = request.form['price']
    image = request.form['image']
    product = Product(name=name, price=price, image=image)
    db.session.add(product)
    db.session.commit()
    return redirect('/admin')

@app.route('/search_booking', methods=['POST'])
def search_booking():
    mobile = request.form['mobile']
    bookings = Booking.query.filter_by(mobile=mobile).all()
    return render_template("bookings.html", bookings=bookings)

@app.route('/edit_item/<int:id>')
def edit_item(id):
    product = Product.query.get(id)
    return render_template("edit_item.html", product=product)

@app.route('/update_item/<int:id>', methods=['POST'])
def update_item(id):
    product = Product.query.get(id)
    product.name = request.form['name']
    product.price = request.form['price']
    product.image = request.form['image']
    db.session.commit()
    return redirect('/admin')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
