FROM python:3.11

RUN apt update && apt install -y \
    libmagic1 \
    vim \
    rsync \
    less \
    git \
    cron

WORKDIR ./app
COPY requirements.txt .
RUN pip install -r ./requirements.txt

COPY exportdb.crontab /etc/cron.d/exportdb
RUN chmod 0644 /etc/cron.d/exportdb \
    && \
    crontab /etc/cron.d/exportdb
