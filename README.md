# GFS Weather Models

Python generated GFS images using Airflow (on AWS EC2) orchestration of ECS tasks on a Fargate cluster. 
Model images are updated four times per day.

* create wxmodels ssh key locally

```
cd ~/.ssh
ssh-keygen -f wxmodels
```

* Go into infra folder and export s3 bucket name you want to use

```
cd infra
export TF_VAR_BUCKET_MODELS=<some_value>
```

* Create resources (takes awhile). Your bucket is used for storing GFS images and `your-bucket-infra` is used by terraform to move the airflow files from local to the EC2. This will build the docker solution in `../models` and push to ECR. It was also create a Fargat cluster, service and task definition. And lastly it will create an Airflow instance on an EC2 with the dags shown in `../airflow.dags`.

```
terraform init -backend-config="bucket=${TF_VAR_BUCKET_MODELS}-infra"
terraform plan
terraform apply -auto-approve
```

* Airflow available locally via port forwarding using the EC2 IP address that is outputted
 
 ```
 ssh -i ~/.ssh/wxmodels -L 8080:localhost:8080 -N ubuntu@<ip_addr_of_ec2>
 ```

 * Browse to the UI and put the dags on so that model runs start populating to S3 on schedule.

 * To destroy resources

 ```
terraform destroy -auto-approve
 ```