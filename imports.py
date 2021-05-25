import csv 
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import datetime
import os 
from application import db,engine

# Check for environment variable


startTime = datetime.datetime.now()

print ( f"starting actions at: {startTime}")

db.execute("drop table IF EXISTS reviews;")
db.execute("drop table IF EXISTS books;")
db.execute("drop table IF EXISTS users;")

db.commit()

#  ======= Creating tables
# books table
db.execute(""" CREATE TABLE IF NOT EXISTS books ( 
    id SERIAL NOT NULL, 
    isbn varchar(100) NOT NULL, 
    title varchar (100) NOT NULL, 
    author varchar(100) NOT NULL, 
    year integer NOT NULL, 
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (isbn) )  """)
print('books table created')

# users table 
db.execute(""" CREATE TABLE IF NOT EXISTS users (
    id SERIAL NOT NULL,
    name varchar(100) NOT NULL, 
    email varchar(100) NOT NULL, 
    password varchar(100) NOT NULL, 
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (id));  """)

print('users table created')
# reviews table 
db.execute(""" CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL NOT NULL,
    user_id INTEGER ,
    name varchar(100) NOT NULL, 
    email varchar(100) NOT NULL, 
    rating varchar(10) NOT NULL, 
    comment varchar(1200) NOT NULL, 
    isbn varchar(100) NOT NULL, 
    FOREIGN KEY (isbn)  REFERENCES books (isbn) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (id)) ;  """)

print('reviews table created')

i = 0
fromFile = open('books.csv')
reader = csv.reader(fromFile)

endtime = None
for isbn, title, author, year in reader:

    i += 1 
    endtime = datetime.datetime.now()

    if title == 'title':
        print (' Skipping 1st row')
    else:
        db.execute(" INSERT INTO public.books (isbn, title, author, year ) VALUES (:a, :b, :c, :d)", {'a':isbn, 'b':title, 'c': author, 'd':year} )
        print ( f"{i} books added successfully at {endtime}")
    # if i==7:
    #     break
# for name, email password in reader2:

        db.commit() 
timeDiff = endtime - startTime
timeDiffSeconds = timeDiff.seconds 
print ( f"Total time to complete action: {timeDiff} ")
print ( f"Total time to complete action in seconds: {timeDiffSeconds} ")