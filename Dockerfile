# syntax=docker/dockerfile:1

FROM python:3.11

ARG HFTOKEN
ENV HFTOKEN_ENV=$HFTOKEN


WORKDIR /code

COPY requirements.txt .

RUN pip3 install pyopenssl
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt
CMD huggingface-cli login --token $HFTOKEN_ENV
CMD huggingface-cli download neuralmind/bert-base-portuguese-cased

COPY . .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app", "--worker-class", "uvicorn.workers.UvicornWorker"]