from flask import Flask, render_template, session, redirect, request, flash
import requests
from flask_sqlalchemy import SQLAlchemy
import hashlib
import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'dzaliandaculikodi'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///application.db"

db = SQLAlchemy(app)

class Links(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80), unique=True, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'{self.username}'

class SavedFacts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fact = db.Column(db.Text)
    image = db.Column(db.Text)
    saved_at = db.Column(db.DateTime)
    author = db.Column(db.Text)

@app.route('/')
def index():
    FACT_LINK = Links.query.filter_by(name='fact').first().link
    IMAGE_LINK = Links.query.filter_by(name='image').first().link
    fact = requests.get(FACT_LINK).json()['data'][0]
    image = requests.get(IMAGE_LINK).json()[0]['url']

    return render_template('index.html', fact=fact, image=image)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect('/')
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
            password = hashlib.sha256(request.form['password'].encode('utf-8')).hexdigest()
            if user.password == password:
                session['logged_in'] = True
                session['username'] = username
                return redirect('/')
            flash("Incorrect Password!")
            return redirect('/login')
        else:
            flash("Incorrect Username!")
            return redirect('/login')
    else:
        return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('logged_in'):
        return redirect('/')
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
            flash("Username Is Already Taken!")
            return redirect('/register')
        password = hashlib.sha256(request.form['password'].encode('utf-8')).hexdigest()
        created_at = datetime.datetime.now()
        user = User(username=username, password=password, created_at=created_at)
        db.session.add(user)
        db.session.commit()
        session['logged_in'] = True
        session['username'] = username
        return redirect('/')
    else:
        return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username',None)
    session.pop('logged_in', None)
    return redirect('/')

@app.route('/mypage')
def mypage():
    if not session.get('logged_in'):
        return redirect('/login')
    else:
        facts = SavedFacts.query.filter_by(author=session['username']).all()
        facts = facts[::-1]
        return render_template('mypage.html', facts=facts)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/save', methods=['post'])
def save():
    if session.get('logged_in'):
        result = request.json
        fact = result['fact']
        image = result['image']
        new_fact = SavedFacts(fact=fact,image=image,saved_at=datetime.datetime.now(),author=session['username'])
        db.session.add(new_fact)
        db.session.commit()
        return redirect('/')
    return redirect('/')


@app.route('/delete', methods=['POST'])
def delete():
    if session.get('logged_in'):
        result = request.json
        fact_id = int(result['fact_id'])
        fact = SavedFacts.query.filter_by(id=fact_id).first()
        db.session.delete(fact)
        db.session.commit()
        return redirect('/mypage')
    return redirect('/')

if __name__ == "__main__":
    # with app.app_context():
    #     db.create_all()
    app.run(debug=True, port=8080)