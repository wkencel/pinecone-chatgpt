Here we have a chatbot REST API using FastAPI that integrates ChatGPT and pinecone using embeddings. The data we should ingest and vectorize are the articles from https://www.alpinehomeair.com/learning-center/. We want this API to be used in a chat UI to answer any questions based on the learning center articles.

To run this file1. 

1. Run the following command to install all the modules listed in the file:
```
pip install -r requirements.txt
```

2. create a .env file and add your environment variables (see .env.example for reference)

3. run the app with the command
```
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. Test the API on Postman
API:

- Postman

```
method: POST
URL: http://127.0.0.1/8000/article
body: { "article": "test test" }
```

- Curl

```
curl -X 'POST' \
  'http://127.0.0.1:8000/article' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "article": "test test"
}'
```