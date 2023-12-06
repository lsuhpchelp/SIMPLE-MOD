FROM ubuntu:20.04

MAINTAINER Jason Li <jasonli3@lsu.edu>

LABEL    software="CAMP" \ 
    base_image="ubuntu:20.04" \ 
    container="CAMP" \ 
    about.summary="CAMP is a QT-based GUI software tool to automatically generate module keys for container-based software packages." \ 
    about.home="https://github.com/lsuhpchelp/CAMP" \ 
    software.version="1.0"

# Install dependencies

RUN apt update
RUN DEBIAN_FRONTEND="noninteractive" apt install -y qt5-default
RUN ln -fs /usr/share/zoneinfo/America/Chicago /etc/localtime
RUN dpkg-reconfigure --frontend noninteractive tzdata
RUN apt install -y python3 pip git
RUN apt clean

RUN pip install --upgrade pip
RUN pip3 install pyqt5
RUN pip3 cache purge


                