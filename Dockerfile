FROM ubuntu:jammy
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -yq install python3-pip
COPY . /engine/
RUN pip3 install -r /engine/requirements.txt
RUN python3 /engine/tests/test.py

CMD ["python3", "/engine/main.py", "--history", "/engine/history.csv"]