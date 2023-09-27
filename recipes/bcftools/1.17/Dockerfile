FROM staphb/bcftools:1.18

MAINTAINER Jason Li <jasonli3@lsu.edu>

LABEL    software="bcftools" \ 
    base_image="quay.io/biocontainers/bcftools:1.17--h3cc50cf_1" \ 
    container="Bcftools" \ 
    about.summary="BCFtools is a program for variant calling and manipulating files in the Variant Call Format (VCF) and its binary counterpart BCF." \ 
    about.home="https://github.com/samtools/bcftools" \ 
    software.version="1.18"

RUN apt update
RUN apt install -y pip
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN pip install matplotlib gffutils 

RUN apt clean
RUN pip cache purge
