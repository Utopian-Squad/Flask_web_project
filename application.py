import os

import requests
from flask import Flask, render_template, url_for, flash, redirect, session, request,jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv
from forms import RegistrationForm, LoginForm,ReviewForm, ProfileForm
from flask_bcrypt import Bcrypt
from functools import wraps



load_dotenv()

app = Flask(__name__)

# Check for environment variable
DATABASE_URL=os.getenv('DATABASE_URL')
SECRET_KEY=os.getenv('SECRET_KEY')

if not(DATABASE_URL):
    raise RuntimeError("DATABASE_URL is not set")


# Configure session to use filesystem

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SECRET_KEY'] = SECRET_KEY
Session(app)

# Set up database
#app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:gregarious11@localhost/books'


engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))

bcrypt = Bcrypt()

bcrypt.init_app(app)

def require_auth(function):
    @wraps(function)
    def wrapper(*args, **kws):
        email = None
        if not 'email' in session:
           
            return redirect(url_for('login'))
            #form = RegistrationForm()
        email = session['email']
        return function(email, *args, **kws)
    return wrapper


@app.route("/")
@require_auth
def index(email):
    try:
        books = db.execute("SELECT * FROM books LIMIT 1").fetchall()
        return render_template("index.html",books=books)
    except:
        return redirect(url_for('error'))



@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    try:
        if form.validate_on_submit():

            username = form.username.data
            password = bcrypt.generate_password_hash(form.password.data).decode("UTF-8")
            email = form.email.data

            db.execute("INSERT INTO users (name, email, password) VALUES (:username, :email, :password)",{
                "username":username , "email":email, "password":password
            })
            db.commit()

            flash(f'Account created for {form.username.data}!', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', title='Register', form=form)
    except:
        return redirect(url_for('error'))

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    email = form.email.data
    password = form.password.data
    try:
        if(form.validate_on_submit()):
            rows = db.execute("SELECT * FROM users WHERE email=:email", {"email": email}).fetchone()

            if rows == None or not bcrypt.check_password_hash(rows[3], password):
                flash('Login Unsuccessful. Please check username and password', 'danger')
                return render_template('login.html', title='Login', form=form)

            else:
                session['id']=rows[0]
                session['name']=rows[1]
                session["email"] = rows[2]
                return redirect(url_for("index"))

        return render_template("/login.html", title="Login", form=form)
    except:
        return redirect(url_for('error'))
@app.route("/logout")
def logout():
    
    session.clear()
    flash('Signed out successfully', 'info')
    return redirect(url_for('login'))


@app.route("/profile", methods=['GET', 'POST'])
# @require_auth
def profile():
    form = ProfileForm()
    try:
        if(form.validate_on_submit()):
            db.execute("UPDATE users SET \
                name = :username,\
                email = :email\
                WHERE id = :id",
                {
                    'username': form.username.data,
                    'email': form.email.data,
                    'id': session['id']
                })
            db.commit()
            session['name']= form.username.data
            return redirect(url_for("index"))
            
        return render_template('profile.html', form=form)
    except:
        return redirect(url_for('error'))

@app.route("/result")
def results():
    try:
        if not request.args.get('book'):
            #todo err page
            return render_template('index.html')
        term = "%"+request.args.get('book')+"%"
        term = term.title()
        limit=10
        page = int(request.args.get('page')) if request.args.get('page') else 1
        
        offset=limit*page-limit

        rows = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                            isbn LIKE :term OR \
                            title LIKE :term OR \
                            author LIKE :term\
                            limit :limit\
                            offset :offset",
                            {
                                "term": term,
                                "offset":offset,
                                "limit":limit,
                            
                            }
                        )
        if(rows.rowcount==0):
            return render_template('index.html')
        else:
            books=rows.fetchall()
            return render_template('result.html',books=books,page=page,numberofbooks=rows.rowcount)
    except:
        return redirect(url_for('error'))


@app.route("/detail/<isbn>",methods=['GET', 'POST'])
@require_auth
def detail(email, isbn):
    form=ReviewForm()
    try:
        if(form.validate_on_submit()):
         

            row2 = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND isbn = :book_id ",
                        {"user_id": session['id'],
                        "book_id": isbn})
            print(row2.fetchone())

          
            
            if row2.rowcount == 1:
                flash('You already submitted a review for this book', 'warning')
                return redirect("/detail/" + isbn)


            db.execute("INSERT INTO reviews (user_id,isbn,name, email, rating, comment) VALUES (:user_id,:isbn,:username, :email, :rating, :content)",{
                "user_id":session['id'],"isbn":isbn,"username":session['name'] , "email":session['email'], "rating":form.rating.data,"content":form.content.data
            })
            db.commit()

        response = requests.get(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}").json()
        #print(response)
        if(response["totalItems"]!=0):
            response=response["items"][0]["volumeInfo"]
            if'averageRating' not in response or 'ratingsCount' not in response:
                response['averageRating'] = 0
                response['ratingsCount'] = 0
        else:
            response={
                "previewLink" : "http://books.google.com/books?id=FITZAQAACAAJ&dq=isbn:0224064924&hl=&cd=1&source=gbs_api",
                "description" : "The description of this book is not avaliable",
                "categories" : "-",
                "pageCount" : "Not Specified",
                "ratingsCount" : 0,
                "averageRating" : 0,
                "imageLinks": "http://covers.openlibrary.org/b/isbn/isbn-M.jpg?default=false"}


        results = db.execute("SELECT isbn, title, author, year FROM books WHERE isbn=:isbn",
                        {
                            "isbn": isbn,
                            
                        }
                    )
        book=results.fetchall()
        book.append(response)
        val = int(book[1]['averageRating'])
        categ=book[1]['categories']
        reviews = db.execute("SELECT name, rating, comment, date FROM reviews WHERE isbn=:isbn",
                        {
                            "isbn": isbn,
                            
                        }
                    )
        all_reviews=reviews.fetchall()
        return render_template("detail.html",book=book,form=form,val=val,all_reviews=all_reviews, rc = reviews.rowcount,categ=categ)
    except:
        return redirect(url_for('error'))

@app.route("/api/v1/<isbn>")
@require_auth
def api(email, isbn):
    try:
        book_api = db.execute("SELECT isbn, title, author, year FROM books WHERE isbn=:isbn",
                        {
                            "isbn": isbn,
                            
                        }).fetchone()
        reviews_api = db.execute("SELECT name, rating ,comment FROM reviews WHERE isbn=:isbn",
                        {
                            "isbn": isbn,                     
                        }
                    )

        reviews_ct=reviews_api.fetchall()

        rcount=reviews_api.rowcount
        sum=0
        
        if (rcount >0):  
            for i in range(rcount):
                current=reviews_ct[i][1]  
                sum+= int(current)     
            average=sum/rcount
        else:
            average=0
        return jsonify({
            'author': book_api['author'],
            'isbn': book_api['isbn'],
            'title': book_api['title'],
            'year': book_api['year'],
            'review':rcount,
            'average_rating':average
            

        })
    except:
        return redirect(url_for('error'))
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/error")
def error():
    
    error = "Something went wrong."
    return render_template("404.html", error=error)

if __name__ == '__main__':
    app.run(debug=True)


# postgresql://postgres:root@localhost:5432/postgres
# DATABASE_URL=postgresql://rftkpnyhfaqmbb:cf6c51a941524c43f79c06bea417c6449ffa194e02b9ab59e82b18a4e0c6a786@ec2-54-167-152-185.compute-1.amazonaws.com:5432/dd9l6jb1u747ot
