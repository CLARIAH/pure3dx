FROM python:3.11

ARG gitlocation
ARG gitbranch
ARG DATA_DIR

RUN apt update && apt install -y \
    libmagic1 \
    vim \
    git

ADD . /app
WORKDIR ./app
RUN pip install -r ./requirements.txt
