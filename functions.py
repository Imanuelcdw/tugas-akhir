import re
import string

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from database import connection
from bson import ObjectId
from googletrans import Translator
from textblob import TextBlob

db = connection()

def cleaning_text(text):
  text = re.sub(r'@[A-Za-z0-9]+', '', text)
  text = re.sub(r'#[A-Za-z0-9]+', '', text)
  text = re.sub(r'RT[\s]', '', text)
  text = re.sub(r"http\S+", '', text)
  text = re.sub(r'[0-9]+', '', text)
  text = re.sub(r'[^A-Za-z ]+', '', text)

  text = text.replace('\n', ' ')
  text = text.translate(str.maketrans('', '', string.punctuation))
  text = text.strip(' ')
  text = text.lower()
  return text

def stemming_text(text):
  factory = StemmerFactory()
  stemmer = factory.create_stemmer()
  return stemmer.stem(text)

def stopwording_text(text):
  factory = StopWordRemoverFactory()
  stopword = factory.create_stop_word_remover()
  return stopword.remove(text)

def translating_text(text):
  translator = Translator()
  result = translator.translate(text).text
  return result

def labeling_text(text):
  if TextBlob(text).sentiment.polarity < 0 :
    result = 'negative'
  else:
    result = 'positive'
  return result



def update_data(tb,obj):
  result = obj.to_dict('records')
  tb = db.get_collection(tb)
  for row in result:
    id = row['_id']['$oid']
    del row['_id']
    tb.find_one_and_update({"_id" : ObjectId(id)},{'$set' : row})
    
  return result