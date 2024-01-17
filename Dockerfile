FROM python:3.11

RUN apt update && apt install -y \
    libmagic1

WORKDIR ./app
ADD . /app
RUN pip install -r ./requirements.txt

WORKDIR ./src
ENTRYPOINT ["./start.sh"]
