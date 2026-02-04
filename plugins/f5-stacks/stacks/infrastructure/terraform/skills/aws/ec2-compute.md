# AWS EC2 Compute

## Overview

Amazon EC2 provides scalable computing capacity. Terraform enables comprehensive EC2 instance management including launch templates, auto scaling, and spot instances.

## EC2 Instance

### Basic Instance

```hcl
resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type

  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.web.id]

  tags = {
    Name = "${var.project}-web"
  }
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}
```

### Production Instance

```hcl
resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.web.id]
  iam_instance_profile   = aws_iam_instance_profile.web.name
  key_name               = var.key_name

  # Root volume
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    iops                  = 3000
    throughput            = 125
    encrypted             = true
    delete_on_termination = true

    tags = {
      Name = "${var.project}-web-root"
    }
  }

  # Additional EBS volume
  ebs_block_device {
    device_name           = "/dev/sdf"
    volume_type           = "gp3"
    volume_size           = 100
    encrypted             = true
    delete_on_termination = true

    tags = {
      Name = "${var.project}-web-data"
    }
  }

  # IMDSv2 (recommended)
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "enabled"
  }

  # Detailed monitoring
  monitoring = true

  # User data
  user_data = base64encode(templatefile("${path.module}/templates/user_data.sh", {
    environment = var.environment
  }))

  tags = {
    Name        = "${var.project}-web"
    Environment = var.environment
  }

  lifecycle {
    ignore_changes = [ami]
  }
}
```

## Launch Template

```hcl
resource "aws_launch_template" "web" {
  name_prefix   = "${var.project}-web-"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type

  vpc_security_group_ids = [aws_security_group.web.id]

  iam_instance_profile {
    name = aws_iam_instance_profile.web.name
  }

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size           = 20
      volume_type           = "gp3"
      encrypted             = true
      delete_on_termination = true
    }
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  monitoring {
    enabled = true
  }

  user_data = base64encode(file("${path.module}/templates/user_data.sh"))

  tag_specifications {
    resource_type = "instance"

    tags = {
      Name        = "${var.project}-web"
      Environment = var.environment
    }
  }

  tag_specifications {
    resource_type = "volume"

    tags = {
      Name = "${var.project}-web-volume"
    }
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project}-web-lt"
  }
}
```

## Auto Scaling Group

### Basic ASG

```hcl
resource "aws_autoscaling_group" "web" {
  name                = "${var.project}-web-asg"
  vpc_zone_identifier = var.subnet_ids
  target_group_arns   = [aws_lb_target_group.web.arn]
  health_check_type   = "ELB"

  min_size         = var.min_size
  max_size         = var.max_size
  desired_capacity = var.desired_capacity

  launch_template {
    id      = aws_launch_template.web.id
    version = "$Latest"
  }

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
    }
  }

  tag {
    key                 = "Name"
    value               = "${var.project}-web"
    propagate_at_launch = true
  }

  lifecycle {
    ignore_changes = [desired_capacity]
  }
}
```

### Mixed Instances ASG

```hcl
resource "aws_autoscaling_group" "web" {
  name                = "${var.project}-web-asg"
  vpc_zone_identifier = var.subnet_ids
  min_size            = 2
  max_size            = 10
  desired_capacity    = 4

  mixed_instances_policy {
    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.web.id
        version            = "$Latest"
      }

      override {
        instance_type = "t3.medium"
      }

      override {
        instance_type = "t3a.medium"
      }

      override {
        instance_type = "t3.large"
      }
    }

    instances_distribution {
      on_demand_base_capacity                  = 1
      on_demand_percentage_above_base_capacity = 25
      spot_allocation_strategy                 = "capacity-optimized"
    }
  }
}
```

## Auto Scaling Policies

### Target Tracking

```hcl
resource "aws_autoscaling_policy" "cpu" {
  name                   = "${var.project}-cpu-scaling"
  autoscaling_group_name = aws_autoscaling_group.web.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }

    target_value = 70.0
  }
}

resource "aws_autoscaling_policy" "alb_requests" {
  name                   = "${var.project}-request-scaling"
  autoscaling_group_name = aws_autoscaling_group.web.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label         = "${aws_lb.web.arn_suffix}/${aws_lb_target_group.web.arn_suffix}"
    }

    target_value = 1000.0
  }
}
```

### Step Scaling

```hcl
resource "aws_autoscaling_policy" "scale_out" {
  name                   = "${var.project}-scale-out"
  autoscaling_group_name = aws_autoscaling_group.web.name
  adjustment_type        = "ChangeInCapacity"
  policy_type            = "StepScaling"

  step_adjustment {
    scaling_adjustment          = 1
    metric_interval_lower_bound = 0
    metric_interval_upper_bound = 20
  }

  step_adjustment {
    scaling_adjustment          = 2
    metric_interval_lower_bound = 20
  }
}

resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "${var.project}-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 120
  statistic           = "Average"
  threshold           = 70

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.web.name
  }

  alarm_actions = [aws_autoscaling_policy.scale_out.arn]
}
```

## Spot Instances

### Spot Instance Request

```hcl
resource "aws_spot_instance_request" "worker" {
  ami                  = data.aws_ami.amazon_linux.id
  instance_type        = "c5.xlarge"
  spot_price           = "0.10"
  wait_for_fulfillment = true

  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.worker.id]

  tags = {
    Name = "${var.project}-spot-worker"
  }
}
```

### Spot Fleet

```hcl
resource "aws_spot_fleet_request" "workers" {
  iam_fleet_role      = aws_iam_role.spot_fleet.arn
  spot_price          = "0.10"
  allocation_strategy = "capacityOptimized"
  target_capacity     = 4

  launch_template_config {
    launch_template_specification {
      id      = aws_launch_template.worker.id
      version = "$Latest"
    }

    overrides {
      instance_type = "c5.large"
      subnet_id     = var.subnet_ids[0]
    }

    overrides {
      instance_type = "c5.large"
      subnet_id     = var.subnet_ids[1]
    }

    overrides {
      instance_type = "c5a.large"
      subnet_id     = var.subnet_ids[0]
    }
  }

  terminate_instances_with_expiration = true
}
```

## IAM Instance Profile

```hcl
resource "aws_iam_role" "ec2" {
  name = "${var.project}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "${var.project}-ec2-role"
  }
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "web" {
  name = "${var.project}-web-profile"
  role = aws_iam_role.ec2.name
}
```

## Application Load Balancer

```hcl
resource "aws_lb" "web" {
  name               = "${var.project}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.environment == "prod"

  tags = {
    Name = "${var.project}-alb"
  }
}

resource "aws_lb_target_group" "web" {
  name     = "${var.project}-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    matcher             = "200"
  }

  tags = {
    Name = "${var.project}-tg"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.web.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.web.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}
```

## Key Pair

```hcl
resource "aws_key_pair" "main" {
  key_name   = "${var.project}-key"
  public_key = file(var.public_key_path)

  tags = {
    Name = "${var.project}-key"
  }
}

# Or generate new key pair
resource "tls_private_key" "main" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "generated" {
  key_name   = "${var.project}-key"
  public_key = tls_private_key.main.public_key_openssh
}

resource "local_sensitive_file" "private_key" {
  filename        = "${path.module}/${var.project}-key.pem"
  content         = tls_private_key.main.private_key_pem
  file_permission = "0600"
}
```

## Outputs

```hcl
output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.web.id
}

output "instance_public_ip" {
  description = "Public IP address"
  value       = aws_instance.web.public_ip
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.web.dns_name
}

output "asg_name" {
  description = "Auto Scaling Group name"
  value       = aws_autoscaling_group.web.name
}
```
