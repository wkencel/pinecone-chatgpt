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
pinecone.init(api_key=PINECODE_KEY, environment=PINECODE_ENVIRONMENT)
vdb = pinecone.Index(PINECODE_DBNAME)

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