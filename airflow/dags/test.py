from datetime import datetime
import logging
import requests
from airflow import DAG
from airflow.operators.python_operator import PythonOperator


default_args = {
    'owner': 'me',
    'depends_on_past': False,
}


dag= DAG('test', default_args=default_args,
         schedule=None, start_date=datetime(2025, 1, 1),
         max_active_runs=1, catchup=False, tags=["test"])


def test(**kwargs):
    resp = requests.get("https://catfact.ninja/fact")
    logging.info(resp.json()["fact"])

test_task = PythonOperator(
    task_id='test',
    python_callable=test,
    dag=dag
)

test_task