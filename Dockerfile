# syntax=docker/dockerfile:1

FROM python:3.11

WORKDIR /code

COPY requirements.txt .

RUN pip3 install pyopenssl 
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt
RUN python3 -m spacy download pt_core_news_sm

COPY . .

CMD uvicorn main:app --port=8080 --host=0.0.0.0