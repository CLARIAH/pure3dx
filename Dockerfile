FROM python:3.11

ARG gitlocation
ARG gitbranch
ARG SECRET_FILE
ARG DATA_DIR
ARG mysecret

RUN apt update && apt install -y \
    vim \
    git

RUN git clone -b ${gitbranch} ${gitlocation} app
WORKDIR ./app
RUN pip install -r ./requirements.txt
RUN echo "${mysecret}" > ${SECRET_FILE}

WORKDIR ./src
ENTRYPOINT ["./start.sh"]
