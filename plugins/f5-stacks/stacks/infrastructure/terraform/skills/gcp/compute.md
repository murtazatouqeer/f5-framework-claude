# GCP Compute Engine

## Overview

Google Compute Engine provides scalable virtual machines. Terraform enables comprehensive configuration of instances, instance templates, managed instance groups, and related resources.

## Compute Instance

### Basic Instance

```hcl
resource "google_compute_instance" "main" {
  name         = "${var.project}-instance"
  machine_type = "e2-medium"
  zone         = "${var.region}-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.main.id

    access_config {
      # Ephemeral public IP
    }
  }

  tags = ["web", "allow-ssh"]

  metadata = {
    enable-oslogin = "TRUE"
  }

  project = var.project_id
}
```

### Production Instance

```hcl
resource "google_compute_instance" "main" {
  name         = "${var.project}-instance"
  machine_type = var.machine_type
  zone         = "${var.region}-a"

  boot_disk {
    initialize_params {
      image = var.image
      size  = 50
      type  = "pd-ssd"
    }
    auto_delete = true
  }

  # Additional disk
  attached_disk {
    source      = google_compute_disk.data.self_link
    device_name = "data"
    mode        = "READ_WRITE"
  }

  network_interface {
    subnetwork = google_compute_subnetwork.main.id
    # No access_config = no public IP
  }

  service_account {
    email  = google_service_account.instance.email
    scopes = ["cloud-platform"]
  }

  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  metadata = {
    enable-oslogin         = "TRUE"
    block-project-ssh-keys = "TRUE"
  }

  metadata_startup_script = file("${path.module}/startup.sh")

  labels = {
    environment = var.environment
    project     = var.project
  }

  tags = ["app", "allow-internal"]

  allow_stopping_for_update = true

  deletion_protection = var.environment == "prod"

  project = var.project_id
}

# Data disk
resource "google_compute_disk" "data" {
  name = "${var.project}-data-disk"
  type = "pd-ssd"
  zone = "${var.region}-a"
  size = 100

  labels = {
    environment = var.environment
  }

  project = var.project_id
}
```

## Instance Template

### Basic Template

```hcl
resource "google_compute_instance_template" "main" {
  name_prefix  = "${var.project}-template-"
  machine_type = var.machine_type

  disk {
    source_image = var.image
    auto_delete  = true
    boot         = true
    disk_type    = "pd-ssd"
    disk_size_gb = 50
  }

  network_interface {
    subnetwork = google_compute_subnetwork.main.id
  }

  service_account {
    email  = google_service_account.instance.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    enable-oslogin = "TRUE"
  }

  tags = ["app"]

  labels = {
    environment = var.environment
  }

  lifecycle {
    create_before_destroy = true
  }

  project = var.project_id
}
```

### Template with Container

```hcl
resource "google_compute_instance_template" "container" {
  name_prefix  = "${var.project}-container-"
  machine_type = "e2-medium"

  disk {
    source_image = "cos-cloud/cos-stable"
    auto_delete  = true
    boot         = true
  }

  network_interface {
    subnetwork = google_compute_subnetwork.main.id
  }

  service_account {
    email  = google_service_account.instance.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    gce-container-declaration = yamlencode({
      spec = {
        containers = [{
          name  = "app"
          image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository}/${var.image}:${var.tag}"
          env = [
            {
              name  = "ENV"
              value = var.environment
            }
          ]
        }]
        restartPolicy = "Always"
      }
    })
  }

  lifecycle {
    create_before_destroy = true
  }

  project = var.project_id
}
```

## Managed Instance Group

### Regional MIG

```hcl
resource "google_compute_region_instance_group_manager" "main" {
  name               = "${var.project}-mig"
  base_instance_name = "${var.project}-instance"
  region             = var.region

  version {
    instance_template = google_compute_instance_template.main.id
  }

  target_size = var.target_size

  named_port {
    name = "http"
    port = 8080
  }

  auto_healing_policies {
    health_check      = google_compute_health_check.main.id
    initial_delay_sec = 300
  }

  update_policy {
    type                           = "PROACTIVE"
    minimal_action                 = "REPLACE"
    most_disruptive_allowed_action = "REPLACE"
    max_surge_fixed                = 3
    max_unavailable_fixed          = 0
    replacement_method             = "SUBSTITUTE"
  }

  instance_lifecycle_policy {
    force_update_on_repair = "YES"
  }

  project = var.project_id
}
```

### MIG with Autoscaler

```hcl
resource "google_compute_region_autoscaler" "main" {
  name   = "${var.project}-autoscaler"
  region = var.region
  target = google_compute_region_instance_group_manager.main.id

  autoscaling_policy {
    max_replicas    = var.max_replicas
    min_replicas    = var.min_replicas
    cooldown_period = 60

    cpu_utilization {
      target = 0.7
    }

    scale_in_control {
      max_scaled_in_replicas {
        fixed = 2
      }
      time_window_sec = 300
    }
  }

  project = var.project_id
}
```

### Custom Metric Autoscaling

```hcl
resource "google_compute_region_autoscaler" "custom" {
  name   = "${var.project}-custom-autoscaler"
  region = var.region
  target = google_compute_region_instance_group_manager.main.id

  autoscaling_policy {
    max_replicas    = var.max_replicas
    min_replicas    = var.min_replicas
    cooldown_period = 60

    metric {
      name   = "pubsub.googleapis.com/subscription/num_undelivered_messages"
      type   = "GAUGE"
      target = 100

      filter = "resource.type=\"pubsub_subscription\" AND resource.label.subscription_id=\"${var.subscription_id}\""
    }
  }

  project = var.project_id
}
```

## Preemptible / Spot Instances

### Spot VM Template

```hcl
resource "google_compute_instance_template" "spot" {
  name_prefix  = "${var.project}-spot-"
  machine_type = var.machine_type

  scheduling {
    preemptible                 = true
    automatic_restart           = false
    provisioning_model          = "SPOT"
    instance_termination_action = "STOP"
  }

  disk {
    source_image = var.image
    auto_delete  = true
    boot         = true
  }

  network_interface {
    subnetwork = google_compute_subnetwork.main.id
  }

  service_account {
    email  = google_service_account.instance.email
    scopes = ["cloud-platform"]
  }

  lifecycle {
    create_before_destroy = true
  }

  project = var.project_id
}
```

## Health Checks

### HTTP Health Check

```hcl
resource "google_compute_health_check" "http" {
  name               = "${var.project}-http-health-check"
  check_interval_sec = 5
  timeout_sec        = 5
  healthy_threshold  = 2
  unhealthy_threshold = 3

  http_health_check {
    port         = 8080
    request_path = "/health"
  }

  project = var.project_id
}
```

### TCP Health Check

```hcl
resource "google_compute_health_check" "tcp" {
  name               = "${var.project}-tcp-health-check"
  check_interval_sec = 5
  timeout_sec        = 5

  tcp_health_check {
    port = 3306
  }

  project = var.project_id
}
```

## Service Account

```hcl
resource "google_service_account" "instance" {
  account_id   = "${var.project}-instance-sa"
  display_name = "Instance Service Account"

  project = var.project_id
}

resource "google_project_iam_member" "instance_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.instance.email}"
}

resource "google_project_iam_member" "instance_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.instance.email}"
}

resource "google_project_iam_member" "instance_storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.instance.email}"
}
```

## Sole-Tenant Nodes

```hcl
resource "google_compute_node_template" "main" {
  name      = "${var.project}-node-template"
  region    = var.region
  node_type = "n1-node-96-624"

  node_affinity_labels = {
    dedicated = var.project
  }

  project = var.project_id
}

resource "google_compute_node_group" "main" {
  name        = "${var.project}-node-group"
  zone        = "${var.region}-a"
  description = "Sole-tenant node group"

  size          = 1
  node_template = google_compute_node_template.main.self_link

  maintenance_policy = "MIGRATE_WITHIN_NODE_GROUP"

  autoscaling_policy {
    mode      = "ONLY_SCALE_OUT"
    min_nodes = 1
    max_nodes = 3
  }

  project = var.project_id
}
```

## GPU Instances

```hcl
resource "google_compute_instance" "gpu" {
  name         = "${var.project}-gpu-instance"
  machine_type = "n1-standard-4"
  zone         = "${var.region}-a"

  boot_disk {
    initialize_params {
      image = "deeplearning-platform-release/tf2-latest-gpu"
      size  = 100
      type  = "pd-ssd"
    }
  }

  guest_accelerator {
    type  = "nvidia-tesla-t4"
    count = 1
  }

  scheduling {
    on_host_maintenance = "TERMINATE"
    automatic_restart   = true
  }

  network_interface {
    subnetwork = google_compute_subnetwork.main.id
  }

  service_account {
    email  = google_service_account.instance.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    install-nvidia-driver = "True"
  }

  project = var.project_id
}
```

## Snapshots and Images

### Snapshot Schedule

```hcl
resource "google_compute_resource_policy" "snapshot" {
  name   = "${var.project}-snapshot-policy"
  region = var.region

  snapshot_schedule_policy {
    schedule {
      daily_schedule {
        days_in_cycle = 1
        start_time    = "04:00"
      }
    }

    retention_policy {
      max_retention_days    = 14
      on_source_disk_delete = "KEEP_AUTO_SNAPSHOTS"
    }

    snapshot_properties {
      labels = {
        automated = "true"
      }
      storage_locations = [var.region]
      guest_flush       = false
    }
  }

  project = var.project_id
}

resource "google_compute_disk_resource_policy_attachment" "main" {
  name = google_compute_resource_policy.snapshot.name
  disk = google_compute_disk.data.name
  zone = "${var.region}-a"

  project = var.project_id
}
```

### Custom Image

```hcl
resource "google_compute_image" "main" {
  name        = "${var.project}-image"
  source_disk = google_compute_disk.main.self_link

  labels = {
    environment = var.environment
  }

  family = "${var.project}-images"

  project = var.project_id
}
```

## Outputs

```hcl
output "instance_id" {
  description = "Instance ID"
  value       = google_compute_instance.main.instance_id
}

output "instance_self_link" {
  description = "Instance self link"
  value       = google_compute_instance.main.self_link
}

output "instance_internal_ip" {
  description = "Instance internal IP"
  value       = google_compute_instance.main.network_interface[0].network_ip
}

output "mig_self_link" {
  description = "MIG self link"
  value       = google_compute_region_instance_group_manager.main.self_link
}

output "mig_instance_group" {
  description = "MIG instance group"
  value       = google_compute_region_instance_group_manager.main.instance_group
}

output "service_account_email" {
  description = "Service account email"
  value       = google_service_account.instance.email
}
```
