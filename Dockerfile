# syntax=docker/dockerfile:1

FROM python:3.11

WORKDIR /code

COPY requirements.txt .

RUN pip3 install pyopenssl
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt
CMD ["python3", "docker_scripts/download_huggingface.py"]

COPY . .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app", "--worker-class", "uvicorn.workers.UvicornWorker"]