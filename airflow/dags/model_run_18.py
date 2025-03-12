from datetime import datetime

from airflow import DAG

from utils import get_all_tasks, get_default_args, config

MODEL_RUN = "18"
SCHEDULE = "45 21 * * *"

with DAG(f"model_run_{MODEL_RUN}",
         default_args=get_default_args(),
         schedule=SCHEDULE,
         start_date=datetime(2025, 3, 7),
         max_active_runs=1,
         catchup=False
         ) as dag:
    
    config(MODEL_RUN) >> get_all_tasks()
