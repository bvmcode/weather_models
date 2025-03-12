from datetime import datetime, timedelta
import boto3
from airflow.providers.amazon.aws.operators.ecs import EcsRunTaskOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.python import get_current_context
from airflow.decorators import task


def get_default_args():
    return {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 5,
    'retry_delay': timedelta(minutes=5),
}


def get_config(model_run, execution_date):
    execution_date_dt = datetime.fromisoformat(str(execution_date))
    today = execution_date_dt.strftime("%Y-%m-%d")
    today = "2025-03-10"
    subnets, security_groups, task_arn = get_cluster_data()
    return {"model_run": model_run,
            "today": today,
            "task_arn": task_arn,
            "subnets": subnets,
            "security_groups": security_groups}


@task(task_id="config")
def config(model_run):
    context = get_current_context()
    return get_config(model_run, context["execution_date"])


def get_hours(start=0):
    hours = [f"{i:03d}" for i in range(0, 121, 6)]
    end = start + len(hours)//7
    return hours[start:end]
    

def get_cluster_data():
    ecs_client = boto3.client("ecs")
    cluster_name = "fargate-cluster"
    service_name = "one-off-service"
    response = ecs_client.describe_services(
        cluster=cluster_name,
        services=[service_name]
    )
    network_config = response["services"][0]["networkConfiguration"]["awsvpcConfiguration"]
    subnets = network_config["subnets"]
    security_groups = network_config["securityGroups"]
    response_task = ecs_client.list_task_definitions(
        familyPrefix="my-task",
        sort="DESC" 
    )
    latest_task_definition_arn = response_task["taskDefinitionArns"][0]
    return subnets, security_groups, latest_task_definition_arn


def produce_ecs_tasks(config_data, hours):
        subnets = config_data["subnets"]
        security_groups = config_data["security_groups"]
        task_arn = config_data["task_arn"]
        model_run = config_data["model_run"]
        tasks = []
        for hour in hours:
            ecs_task = EcsRunTaskOperator(
                task_id="run_ecs_task",
                cluster="fargate-cluster",
                task_definition=task_arn,
                launch_type="FARGATE",
                overrides={
                    "containerOverrides": [
                        {
                            "name": "my-container",
                        "environment": [
                            {"name": "MODEL_RUN", "value": model_run},
                            {"name": "HOUR", "value": hour}
                    ]
                        }
                    ]
                },
                network_configuration={
                    "awsvpcConfiguration": {
                        "subnets": subnets,
                        "securityGroups": security_groups,
                        "assignPublicIp": "ENABLED",
                    }
                },
            )
            tasks.append(ecs_task)
        return tasks


def run_tasks(hour_range, **kwargs):
    ti = kwargs["ti"]
    config_data = ti.xcom_pull(task_ids="config")
    hours = get_hours(hour_range)
    ecs_tasks = produce_ecs_tasks(config_data, hours)
    for ecs_task in ecs_tasks:
        ecs_task.execute(kwargs)


def get_all_tasks():
    ecs_tasks = []
    for i in range(0,19,3):
        ecs_tasks.append(
            PythonOperator(
                task_id=f"run_ecs_{i}",
                python_callable=run_tasks,
                op_kwargs={"hour_range": i},
                provide_context=True
            )
        )
    return ecs_tasks