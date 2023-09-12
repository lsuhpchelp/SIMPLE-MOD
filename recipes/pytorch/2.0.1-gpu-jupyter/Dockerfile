FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

MAINTAINER Jason Li <jasonli3@lsu.edu>

LABEL    software="PyTorch" \ 
    base_image="pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime" \ 
    container="PyTorch" \ 
    about.summary="PyTorch framework for deep learning, with GPU support, QT support, commonly used Python modules such as jupyter." \ 
    about.home="https://pytorch.org/" \ 
    software.version="2.0.1"

RUN apt update
RUN DEBIAN_FRONTEND="noninteractive" apt install -y qt5-default
RUN ln -fs /usr/share/zoneinfo/America/Chicago /etc/localtime
RUN dpkg-reconfigure --frontend noninteractive tzdata
RUN pip install matplotlib==3.7.2 \
                pyqt5==5.15.9 \
                jupyter==1.0.0 \
                Cython==3.0.0 \
                dask==2023.8.0 \
                numba==0.57.1 \
                numexpr==2.8.5 \
                pandas==2.0.3 \
                regex==2023.6.3 \
                scikit-image==0.21.0 \
                scikit-learn==1.3.0 \
                scikit-learn-intelex==2023.2.1
                