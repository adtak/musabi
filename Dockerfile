FROM python:3.8-buster

WORKDIR /opt/app

COPY src/ ./src/
COPY Pipfile .
COPY Pipfile.lock .
COPY setup.py .
COPY setup.cfg .
COPY model/ ./model/

RUN pip install pipenv && pipenv install -e . --skip-lock

CMD pipenv run python src/job/insta_job.py -m model -i image
