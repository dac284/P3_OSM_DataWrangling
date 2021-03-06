"""
Your task is to sucessfully run the exercise to see how pymongo works
and how easy it is to start using it.
You don't actually have to change anything in this exercise,
but you can change the city name in the add_city function if you like.

Your code will be run against a MongoDB instance that we have provided.
If you want to run this code locally on your machine,
you have to install MongoDB (see Instructor comments for link to installation information)
and uncomment the get_db function.
"""

"""
def get_db():
    from pymongo import MongoClient
    client = MongoClient('localhost:27017')
    # 'examples' here is the database name. It will be created if it does not exist.
    db = client.examples
    return db
"""
import sys

def add_city(db, file_in):
    db.SDT.insert(file_in)
    
def get_city(db):
    return db.SDT.find_one()

def get_db():
    # For local use
    from pymongo import MongoClient
    client = MongoClient('localhost:27017')
    # 'examples' here is the database name. It will be created if it does not exist.
    db = client.OSM
    return db

if __name__ == "__main__":
    file_in = sys.argv[1]
    db = get_db() # uncomment this line if you want to run this locally
    add_city(db,file_in)
    print get_city(db)