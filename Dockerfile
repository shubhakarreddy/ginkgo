FROM ubuntu:18.04

ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /home

# Copy over required files
ADD ./requirements.txt /home

# Initial prep
RUN apt-get update -y && apt-get install --no-install-recommends apt-utils -y

RUN apt-get install python3 python3-dev python3-pip -y

RUN apt-get install libssl-dev -y
RUN apt-get install libmysqlclient-dev -y

RUN python3 -m pip install -r requirements.txt
