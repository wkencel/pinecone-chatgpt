import os
import openai
import json
import re
import pinecone
from dotenv import load_dotenv
from time import sleep
from uuid import uuid4
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from article_scraper import get_article_urls, get_article_content

# Load environment variables from .env
load_dotenv()

class DBParams(BaseModel):
  title: str
  body: str

class RequestParams(BaseModel):
  question: str

load_dotenv()
OPENAI_KEY = os.environ.get("OPENAI_KEY")
PINECODE_KEY = os.environ.get("PINECODE_KEY")
PINECODE_DBNAME = os.environ.get("PINECODE_DBNAME")
PINECODE_ENVIRONMENT = os.environ.get("PINECODE_ENVIRONMENT")

convo_length = 8
openai.api_key = OPENAI_KEY

# Create the pinecone vector database
pinecone.init(api_key=PINECODE_KEY, environment=PINECODE_ENVIRONMENT)
# uncomment these lines of code if it's your first time running. needed to create the pinecone index

# # delete the pinecone index in case it already exists
# pinecone.delete_index(PINECODE_DBNAME)
# # create the pinecone index
# pinecone.create_index(PINECODE_DBNAME, dimension=8, metric="euclidean")
# #  print info of pinecone db
# print(pinecone.list_indexes())
# pinecone.describe_index(PINECODE_DBNAME)

vdb = pinecone.Index(index_name=PINECODE_DBNAME)

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": "Make a post request to /article to ask a question by virtual assistant"
    }
# @app.post("/article")
# def create_answer(params: RequestParams):
#     question = params.article
#     if question == '':
#         return {"type": "error"}
#     else:  
#         vector = gpt3_embedding(question) # Get embedding for the question
#         results = vdb.query(vector=vector, top_k=convo_length) # Find the closest vectors in the vector database
#         articles = load_articles(results) # Load the articles related to those vectors
#         prompt = PROMPT_RESPONSE.replace('<TITLE>', question).replace('<ARTICLE>', articles) # Formulate the prompt for GPT-3
#         output = gpt3_completion(prompt) # Generate the response from GPT-3
#         return { "answer": output }

# def load_articles(results):
#     result = list()
#     for m in results['matches']:
#         info = load_data('%s/%s.db' % (DB_FOLDER, m['id'])) # Load the relevant articles
#         result.append(info['article']) # Extract the article text

def extract_article_text_save_to_db():
  articles_urls = get_article_urls()
  payload = []

  for url in articles_urls:
    article = get_article_content(url)
    vector = gpt3_embedding(article) # Get embeddings for the articles
    unique_id = str(uuid4())
    metadata = {'uuid': unique_id, 'article': article }
    save_data('%s/%s.db' % (DB_FOLDER, unique_id), metadata) # save a local copy of the article
    payload.append((unique_id, vector))  # add to the payload
  vdb.upsert(payload)

extract_article_text_save_to_db()

@app.post("/db")
def create_db(params: DBParams):
  title = params.title
  body = params.body
  vector = gpt3_embedding(title)
  unique_id = str(uuid4())
  metadata = {
    "title": title,
    "body": body
  }
  payload = list()
  payload.append((unique_id, vector, metadata))
  try:
    vdb.upsert(payload)
    return { "status": "ok" }
  except:
    return { "status": "failed"}

@app.post("/article")
def article(params: RequestParams):
  question = params.question
  if question == '':
    return { "type": "error" }
  else:
    vector = gpt3_embedding(question)
    try:
      results = vdb.query(vector=vector, top_k=convo_length, include_metadata=True)
      uuid, answer = load_answer(results)
      return {"status": "ok", "uuid": uuid, "answer": answer}
    except:
      return {"status": "failed"}

def gpt3_embedding(content, engine='text-embedding-ada-002'):
  content = content.encode(encoding='ASCII',errors='ignore').decode()
  response = openai.Embedding.create(input=content,engine=engine)
  vector = response['data'][0]['embedding']
  return vector

def load_answer(results):
  highest_score = -float('inf')
  metadata_with_highest_score = None
  body_of_highest_score = ""
  uuid = ""

  for match in results['matches']:
    if match['score'] > highest_score:
        highest_score = match['score']
        metadata_with_highest_score = match['metadata']
        uuid = match['id']
  
  if metadata_with_highest_score is not None:
    body_of_highest_score = metadata_with_highest_score['body']
  
  return uuid, body_of_highest_score