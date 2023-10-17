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

class RequestParams(BaseModel):
  article: str

load_dotenv()
OPENAI_KEY = os.environ.get("OPENAI_KEY")
PINECODE_KEY = os.environ.get("PINECODE_KEY")
PINECODE_DBNAME = os.environ.get("PINECODE_DBNAME")
PINECODE_ENVIRONMENT = os.environ.get("PINECODE_ENVIRONMENT")
PROMPT_RESPONSE = os.environ.get("PROMPT_RESPONSE")
DB_FOLDER = os.environ.get("DB_FOLDER")

if not os.path.exists(DB_FOLDER):
  os.mkdir(DB_FOLDER)

convo_length = 30
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
        "message": "Make a post request to /ask to ask a question by virtual pastor"
    }

@app.post("/article")
def create_answer(params: RequestParams):
  question = params.article
  if question == '':
    return { "type": "error" }
  else:    
    payload = list()
    vector = gpt3_embedding(question)
    unique_id = str(uuid4())
    metadata = {'uuid': unique_id, 'message': question }
    save_data('%s/%s.db' % (DB_FOLDER, unique_id), metadata)
    payload.append((unique_id, vector))
    results = vdb.query(vector=vector, top_k=convo_length)
    conversation = load_conversation(results)
    prompt = PROMPT_RESPONSE.replace('<TITLE>', question).replace('<ARTICLE>', conversation)
    output = gpt3_completion(prompt)
    question = output
    vector = gpt3_embedding(question)
    unique_id = str(uuid4())
    metadata = {'message': question, 'uuid': unique_id}
    save_data('%s/%s.db' % (DB_FOLDER, unique_id), metadata)
    payload.append((unique_id, vector))
    vdb.upsert(payload)
    return { "answer": output }
  


def load_data(filepath):
  with open(filepath, 'r', encoding='utf-8') as infile:
    return json.load(infile)

def save_data(filepath, payload):
  with open(filepath, 'w', encoding='utf-8') as outfile:
    json.dump(payload, outfile, ensure_ascii=False, sort_keys=True, indent=2)

def gpt3_embedding(content, engine='text-embedding-ada-002'):
  content = content.encode(encoding='ASCII',errors='ignore').decode()
  print("content=", content)
  response = openai.Embedding.create(input=content,engine=engine)
  vector = response['data'][0]['embedding']
  return vector

def gpt3_completion(prompt, engine='text-davinci-003', temp=0.0, top_p=1.0, tokens=400, freq_pen=0.0, pres_pen=0.0, stop=['Article:']):
  max_retry = 5
  retry = 0
  prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()
  while True:
    try:
      response = openai.Completion.create(
        engine=engine,
        prompt=prompt,
        temperature=temp,
        max_tokens=tokens,
        top_p=top_p,
        frequency_penalty=freq_pen,
        presence_penalty=pres_pen,
        stop=stop)
      text = response['choices'][0]['text'].strip()
      text = re.sub('[\r\n]+', '\n', text)
      text = re.sub('[\t ]+', ' ', text)
      return text
    except Exception as oops:
      retry += 1
      if retry >= max_retry:
          return "GPT3 error: %s" % oops
      print('Error communicating with OpenAI:', oops)
      sleep(1)

def load_conversation(results):
  result = list()
  for m in results['matches']:
    info = load_data('db/%s.db' % m['id'])
    result.append(info)
  ordered = sorted(result, key=lambda d: d['time'], reverse=False)
  messages = [i['message'] for i in ordered]
  return '\n'.join(messages).strip()