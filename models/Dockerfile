FROM --platform=linux/amd64 python:3.12-slim

# Install dependencies for eccodes, including gfortran
RUN apt-get update && apt-get install -y \
    g++ \
    gfortran \ 
    libgeos-dev \
    libeccodes-dev \
    libeccodes0 \
    wget \
    cmake \
    build-essential \
    libpng-dev \
    libopenjp2-7-dev \
    && apt-get clean

# Manually install eccodes from ECMWF
RUN wget https://confluence.ecmwf.int/download/attachments/45757960/eccodes-2.34.0-Source.tar.gz -O /tmp/eccodes.tar.gz && \
    cd /tmp && \
    tar -xzf eccodes.tar.gz && \
    cd eccodes-2.34.0-Source && \
    mkdir build && cd build && \
    cmake .. && \
    make && make install && \
    ldconfig && \
    cd / && rm -rf /tmp/eccodes*

# Set environment variables for eccodes
ENV ECCODES_DEFINITION_PATH=/usr/local/share/eccodes/definitions
ENV ECCODES_SAMPLES_PATH=/usr/local/share/eccodes/samples
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY ./src ./src
WORKDIR /app/src

ENTRYPOINT ["python", "main.py"]