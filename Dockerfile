# syntax=docker/dockerfile:1

FROM python:3.11

WORKDIR /code

COPY requirements.txt .

RUN pip3 install pyopenssl 
RUN pip3 install -r requirements.txt
RUN python3 -m spacy download https://github.com/explosion/spacy-models/releases/download/pt_core_news_sm-3.8.0/pt_core_news_sm-3.8.0-py3-none-any.whl

COPY . .

EXPOSE 3100

CMD ["gunicorn", "--bind", "0.0.0.0:3100", "main:app", "--worker-class", "uvicorn.workers.UvicornWorker"]