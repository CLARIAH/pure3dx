FROM python:3.11

ARG gitlocation
ARG gitbranch
ARG DATA_DIR

RUN apt update && apt install -y \
    libmagic1 \
    vim \
    rsync \
    less \
    git

WORKDIR ./app
COPY requirements.txt .
RUN pip install -r ./requirements.txt
