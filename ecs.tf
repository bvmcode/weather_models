

resource "aws_cloudwatch_log_group" "ecs_logs" {
  name = "/ecs/wxmodels"
  retention_in_days = 7 
}


resource "aws_security_group" "ecs_sg" {
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}


resource "aws_iam_role" "ecs_task_execution_role" {
  name = "ecsTaskExecutionRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}


resource "aws_iam_role_policy_attachment" "ecs_s3_attach" {
  policy_arn = aws_iam_policy.s3_rw_policy.arn
  role       = aws_iam_role.ecs_task_execution_role.name
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_attach" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
  role       = aws_iam_role.ecs_task_execution_role.name
}


resource "aws_ecs_cluster" "main" {
  name = "fargate-cluster"
}


resource "aws_ecs_task_definition" "my_task" {
  family                   = "my-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "4096"
  memory                   = "8192"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_execution_role.arn 
  ephemeral_storage {
    size_in_gib = 50
  }
  container_definitions = jsonencode([{
    name      = "my-container"
    image     = "122887972227.dkr.ecr.us-east-1.amazonaws.com/weather_models:latest"
    cpu     = 4096
    memory   = 8192
    essential = true
    

    portMappings = [{
      containerPort = 80
      hostPort      = 80
      protocol      = "tcp"
    }]
        logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = "/ecs/wxmodels"
        awslogs-region        = "us-east-1"
        awslogs-stream-prefix = "ecs"
      }
    }
    environment = [
      { name = "S3_BUCKET_NAME", value = "bvm-wx-models" }
    ]
  }])
}


resource "aws_iam_policy" "ecs_logs_policy" {
  name        = "ECSLogsPolicy"
  description = "Allows ECS tasks to write logs to CloudWatch"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      Resource = "arn:aws:logs:us-east-1:122887972227:log-group:/ecs/wxmodels:*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_logs_attach" {
  policy_arn = aws_iam_policy.ecs_logs_policy.arn
  role       = aws_iam_role.ecs_task_execution_role.name
}


resource "aws_ecs_service" "one_off_service" {
  name            = "one-off-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.my_task.arn
  launch_type     = "FARGATE"
  desired_count   = 0
  platform_version = "1.4.0"
  network_configuration {
    subnets          = [aws_subnet.public.id]
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }
}
