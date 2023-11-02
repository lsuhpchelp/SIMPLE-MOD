FROM horovod/horovod:0.28.1

MAINTAINER Jason Li <jasonli3@lsu.edu>

LABEL    software="Horovod" \ 
    base_image="horovod/horovod:0.28.1" \ 
    container="Tensorflow" \ 
    about.summary="Distributed training framework for TensorFlow, Keras, PyTorch, and Apache MXNet." \ 
    about.home="https://www.tensorflow.org/" \ 
    software.version="0.28.1"

RUN apt update
RUN apt install -y qt5-default
RUN pip install pyqt5==5.15.9 \
                jupyterlab==4.0.4 \
                Cython==3.0.0 \
                dask==2023.5.0 \
                numba==0.57.1 \
                numexpr==2.8.5 \
                regex==2023.6.3 \
                scikit-image==0.21.0 \
                scikit-learn==1.3.0 \
                scikit-learn-intelex==2023.2.1 \
                scipy==1.10.1 \
                sympy==1.12

RUN apt clean
RUN pip cache purge
