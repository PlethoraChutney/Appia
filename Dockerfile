FROM python:3.9.1-slim-buster

WORKDIR /traces

COPY web-requirements.txt web-requirements.txt
RUN python -m pip install -r web-requirements.txt

COPY . .
EXPOSE 8080
CMD ["gunicorn", "-b", ":8080", "--workers=8", "web:app"]
