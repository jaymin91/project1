import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker

engine = create_engine("postgres://flqifujrhvgfqx:60d1e37710fcda3dfc4e3afaac7309817f48992e120b808692d711bf1b6150e2@ec2-18-233-32-61.compute-1.amazonaws.com:5432/d3mb3eorevq7e9")
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    read = csv.reader(f)
    for isbn,title,author,year in read:
        db.execute("INSERT INTO books (isbn, title, author, year) values (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": year})
        
    db.commit()

if __name__=="__main__":
    main()


