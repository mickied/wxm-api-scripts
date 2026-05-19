FROM python:3.12.1-slim

WORKDIR /usr/src/app

RUN pip install --no-cache-dir \
	mysql-connector-python \
	requests

COPY wxm_docker.py base_functions.py ./

CMD ["python", "wxm_docker.py"]