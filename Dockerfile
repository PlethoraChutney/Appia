FROM python:3.9.1-slim-buster

WORKDIR /traces

RUN python -m pip install appia dash gunicorn

COPY . .
EXPOSE 8080
CMD ["bash", "./docker_launch.sh"]
