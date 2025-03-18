resource "aws_security_group" "ssh_only" {
  name        = "ssh_only"
  description = "Allow SSH and Airflow UI inbound traffic"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["127.0.0.1/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_key_pair" "deployer" {
  key_name   = "my-key"
  public_key = file("~/.ssh/wxmodels.pub")
}

resource "null_resource" "airflow_to_s3" {
  provisioner "local-exec" {
    command = "bash ./scripts/airflow_to_s3.sh"
    when = create
  }
}

resource "aws_iam_policy" "ecs_execution_policy" {
  name        = "ECSExecutionPolicy"
  description = "Allows Airflow on EC2 to manage ECS tasks"
  
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ecs:DescribeServices",
          "ecs:DescribeClusters",
          "ecs:ListServices",
          "ecs:DescribeTaskDefinition",
          "ecs:RunTask",
          "ecs:StopTask",
          "ecs:ListTaskDefinitions",
          "ecs:ListTasks",
          "ecs:DescribeTasks"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "iam:PassRole"
        ],
        Resource = "*"
      }
    ]
  })
}


resource "aws_iam_role_policy_attachment" "ecs_execution_attach" {
  role       = aws_iam_role.ec2_s3_role.name
  policy_arn = aws_iam_policy.ecs_execution_policy.arn
}


resource "aws_iam_role" "ec2_s3_role" {
  name = "ec2_s3_access_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}


resource "aws_iam_role_policy_attachment" "ec2_s3_attachment" {
  role       = aws_iam_role.ec2_s3_role.name
  policy_arn = aws_iam_policy.s3_rw_policy.arn
}

resource "aws_iam_instance_profile" "ec2_instance_profile" {
  name = "ec2_s3_instance_profile"
  role = aws_iam_role.ec2_s3_role.name
}


resource "aws_instance" "web" {
  ami                    = "ami-0e1bed4f06a3b463d"
  instance_type          = "m5.2xlarge"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.ssh_only.id]
  key_name               = aws_key_pair.deployer.key_name
  iam_instance_profile   = aws_iam_instance_profile.ec2_instance_profile.name

  user_data = <<-EOF
            #!/bin/bash
            apt-get update
            apt-get install -y docker.io docker-compose
            mkdir -p /home/ubuntu/airflow
            mkdir -p /home/ubuntu/airflow/dags
            cd /home/ubuntu/airflow
            apt-get install awscli -y
            aws s3 cp s3://${var.BUCKET_MODELS}-infra/airflow/docker-compose.yml docker-compose.yaml
            aws s3 cp s3://${var.BUCKET_MODELS}-infra/airflow/Dockerfile Dockerfile
            aws s3 cp s3://${var.BUCKET_MODELS}-infra/airflow/requirements.txt requirements.txt
            aws s3 cp s3://${var.BUCKET_MODELS}-infra/airflow/dags/test.py ./dags/test.py
            aws s3 cp s3://${var.BUCKET_MODELS}-infra/airflow/dags/model_run_00.py ./dags/model_run_00.py
            aws s3 cp s3://${var.BUCKET_MODELS}-infra/airflow/dags/model_run_06.py ./dags/model_run_06.py
            aws s3 cp s3://${var.BUCKET_MODELS}-infra/airflow/dags/model_run_12.py ./dags/model_run_12.py
            aws s3 cp s3://${var.BUCKET_MODELS}-infra/airflow/dags/model_run_18.py ./dags/model_run_18.py
            aws s3 cp s3://${var.BUCKET_MODELS}-infra/airflow/dags/utils.py ./dags/utils.py
            chmod 666 /var/run/docker.sock
            sudo su ubuntu
            sudo groupadd docker
            sudo gpasswd -a $USER docker
            chown ubuntu:ubuntu /home/ubuntu/airflow/docker-compose.yaml
            sudo chmod u=rwx,g=rwx,o=rwx /home/ubuntu/airflow/logs
            cd /home/ubuntu/airflow
            export AIRFLOW_UID=5000
            export BUCKET_NAME=${var.BUCKET_MODELS}
            docker-compose up -d
              EOF

  tags = {
    Name = "Airflow-EC2"
  }
}

output "instance_public_ip" {
  value = aws_instance.web.public_ip
}
