FROM python:3.8-buster

WORKDIR /opt/app

COPY src/ ./src/
COPY Pipfile .
COPY Pipfile.lock .
COPY setup.py .
COPY setup.cfg .
COPY model/ ./model/

RUN pip install pipenv && pipenv install -e .

CMD ["pipenv run python insta_job.py"]
