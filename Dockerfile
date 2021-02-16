FROM python:3.9.1-slim-buster

WORKDIR /traces

COPY requirements.txt requirements.txt
RUN python -m pip install -r requirements.txt

COPY . .
EXPOSE 8080
CMD ["python3", "./waitress_serve.py"]
