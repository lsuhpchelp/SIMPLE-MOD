FROM tensorflow/tensorflow:2.13.0-gpu-jupyter

MAINTAINER Jason Li <jasonli3@lsu.edu>

LABEL    software="Tensorflow" \ 
    base_image="tensorflow/tensorflow:2.13.0-gpu-jupyter" \ 
    container="Tensorflow" \ 
    about.summary="Tensorflow framework for deep learning, with GPU support, QT support, commonly used Python modules such as jupyter." \ 
    about.home="https://www.tensorflow.org/" \ 
    software.version="2.13.0"

RUN apt update
RUN apt install -y qt5-default
RUN pip install pyqt5==5.15.9 \
                jupyterlab==4.0.4 \
                Cython==3.0.0 \
                dask==2023.5.0 \
                numba==0.57.1 \
                numexpr==2.8.5 \
                pandas==2.0.3 \
                regex==2023.6.3 \
                scikit-image==0.21.0 \
                scikit-learn==1.3.0 \
                scikit-learn-intelex==2023.2.1 \
                scipy==1.10.1 \
                sympy==1.12 \
                tqdm==4.65.0

RUN apt clean
RUN pip cache purge
