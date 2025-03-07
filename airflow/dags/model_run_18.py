from datetime import datetime, timedelta

from airflow import DAG
from airflow.decorators import task

from utils import get_config, run_tasks

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 5,
    'retry_delay': timedelta(minutes=5),
}

with DAG("model_run_18", default_args=default_args,
         schedule="45 21 * * *",
         start_date=datetime(2025, 3, 1),
         max_active_runs=1,
         catchup=False
         ) as dag:


    @task(task_id="config")
    def config(**kwargs):
        return get_config("18", kwargs["execution_date"])


    @task(task_id="run_ecs_0")
    def run_ecs_0(**kwargs):
        run_tasks(0, **kwargs)


    @task(task_id="run_ecs_3")
    def run_ecs_3(**kwargs):
        run_tasks(3, **kwargs)


    @task(task_id="run_ecs_6")
    def run_ecs_6(**kwargs):
        run_tasks(6, **kwargs)


    @task(task_id="run_ecs_9")
    def run_ecs_9(**kwargs):
        run_tasks(9, **kwargs)


    @task(task_id="run_ecs_12")
    def run_ecs_12(**kwargs):
        run_tasks(12, **kwargs)


    @task(task_id="run_ecs_15")
    def run_ecs_15(**kwargs):
        run_tasks(15, **kwargs)


    @task(task_id="run_ecs_18")
    def run_ecs_18(**kwargs):
        run_tasks(18, **kwargs)


    config() >> [run_ecs_0(), run_ecs_3(), run_ecs_6(),
                 run_ecs_9(), run_ecs_12(), run_ecs_15(),
                 run_ecs_18()]
