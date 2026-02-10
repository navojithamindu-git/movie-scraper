import pymongo
import pandas as pd

class DataStore:
    def __init__(self, mongo_uri, db_name, collection_name):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def insert_movie(self, movie):
        self.collection.insert_one(movie)

    def export_to_excel(self, movies, filename="scraped_movies.xlsx"):
        df = pd.DataFrame(movies)
        df.to_excel(filename, index=False)
