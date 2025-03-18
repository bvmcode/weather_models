
S3_BUCKET=${TF_VAR_BUCKET_MODELS}

aws s3 cp ../airflow/docker-compose.yaml s3://$S3_BUCKET-infra/airflow/docker-compose.yml
aws s3 cp ../airflow/Dockerfile s3://$S3_BUCKET-infra/airflow/Dockerfile
aws s3 cp ../airflow/requirements.txt s3://$S3_BUCKET-infra/airflow/requirements.txt
aws s3 cp ../airflow/dags/test.py s3://$S3_BUCKET-infra/airflow/dags/test.py
aws s3 cp ../airflow/dags/model_run_00.py s3://$S3_BUCKET-infra/airflow/dags/model_run_00.py
aws s3 cp ../airflow/dags/model_run_06.py s3://$S3_BUCKET-infra/airflow/dags/model_run_06.py
aws s3 cp ../airflow/dags/model_run_12.py s3://$S3_BUCKET-infra/airflow/dags/model_run_12.py
aws s3 cp ../airflow/dags/model_run_18.py s3://$S3_BUCKET-infra/airflow/dags/model_run_18.py
aws s3 cp ../airflow/dags/utils.py s3://$S3_BUCKET-infra/airflow/dags/utils.py
