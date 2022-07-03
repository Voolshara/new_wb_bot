FROM python:3.9

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock

RUN apt-get -y update \
 && apt-get -y upgrade \

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install poetry
RUN poetry config virtualenvs.create false

COPY . .
RUN poetry install
