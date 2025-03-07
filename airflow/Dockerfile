FROM apache/airflow:slim-2.9.3-python3.10
USER root
COPY requirements.txt .
USER airflow
#RUN pip3.10 install --upgrade pip setuptools wheel
RUN pip3.10 install -r requirements.txt
RUN pip3.10 check
RUN airflow db upgrade