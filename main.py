import os
import json
import pandas as pd
from flask import Flask, request
from dotenv import load_dotenv
from bson import json_util
from functions import *
from database import connection
from time import time
from flask_cors import CORS, cross_origin

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

load_dotenv()
app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
db = connection()

### ROUTES
## BEGIN BASIC CRUD
# Home
@app.route("/")
@cross_origin()
def hello_world():
    return f'API {os.getenv('APP_NAME')}'

# GET table list
@app.route("/api/data", methods=['GET'])
def table_list():
    tb = db.get_collection('table_list')
    data = tb.find({})
    return json.loads(json_util.dumps(data)) 

# GET table contains
@app.route("/api/data/<tb>", methods=['GET'])
def find_all(tb):
    tb = db.get_collection(tb)
    data = tb.find({})
    return json.loads(json_util.dumps(data)) 

# POST upload data
@app.route("/api/data", methods=['POST'])
def upload_many():
    file = json.load(request.files['dataset'])
    form = request.form.to_dict()
    data = []
    for row in file:
        data.append({
            "text" : row['full_text'],
            "date" : row['created_at'],
            "url" : row['tweet_url'],
            "username" : row['username'],
            "location" : form['location']
        })
    tb = db.get_collection(form['table'])
    try:
        tb.insert_many(data)
        db.get_collection('table_list').insert_one({'name' : form['table']})
    except Exception as e:
        print(e)
    return json.loads(json_util.dumps(data)) 

# DELETE table 
@app.route("/api/drop/<tb>", methods=['DELETE'])
def drop_table(tb):
    try:
        db.drop_collection(tb)
        db.get_collection('table_list').delete_one({'name' : tb})
    except Exception as e:
        print(e)
    return f'droped table {tb}'
## END


## BEGIN LOGIC RANDOM FOREST

# cleaning
# stemming
# stopword
# translate
# label
# tfidf
# test train split
# accuracy

@app.route("/api/train/<tb>", methods=['GET'])
def training(tb):
    data = find_all(tb)
    
    df = pd.DataFrame(data)
    start_time = time()

    if 'cleaned' not in df.columns : 
        df['cleaned'] = df['text'].apply(cleaning_text)
        update_data(tb, df)
    
    if 'stopworded' not in df.columns : 
        df['stopworded'] = df['cleaned'].apply(stopwording_text)
        update_data(tb, df)

    if 'stemmed' not in df.columns : 
        df['stemmed'] = df['stopworded'].apply(stemming_text)
        update_data(tb, df)

    if 'translated' not in df.columns : 
        for row in df.to_dict('records'):
            df.loc[df['stemmed'] == row['stemmed'], 'translated'] = translating_text(row['stemmed'])
        update_data(tb, df)

    if 'sentiment' not in df.columns : 
        df['sentiment'] = df['translated'].apply(labeling_text)
        update_data(tb, df)

    tfidf = TfidfVectorizer(max_features=1000, binary=True)
    vector = tfidf.fit_transform(df['stemmed'])
    
    X = df['stemmed']
    Y = df['sentiment']

    X_train, X_test, Y_train, Y_test = train_test_split(vector, Y, test_size=0.3)

    model = RandomForestClassifier(n_estimators=200, random_state=0)
    model.fit(X_train, Y_train)

    predictions = model.predict(X_test)

    end_time = time()
    print(f'load time:{round(end_time-start_time, 3)} s')
    
    return f"accuracy : {accuracy_score(Y_test, predictions)}"