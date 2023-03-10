FROM python:3.11

RUN apt update && apt install -y \
    vim \
    git

RUN git clone -b ${gitbranch} ${gitlocation} app
RUN pip install -r ./requirements.txt

WORKDIR ./src
ENTRYPOINT ["./start.sh"]
