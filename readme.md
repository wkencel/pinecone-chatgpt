How to run?

```
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

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