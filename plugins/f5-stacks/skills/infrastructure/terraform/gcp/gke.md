# GCP GKE (Google Kubernetes Engine)

## Overview

Google Kubernetes Engine provides managed Kubernetes clusters. Terraform enables comprehensive GKE configuration including node pools, Autopilot mode, and cluster add-ons.

## GKE Cluster

### Standard Cluster

```hcl
resource "google_container_cluster" "main" {
  name     = "${var.project}-cluster"
  location = var.region

  # Remove default node pool
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.main.name
  subnetwork = google_compute_subnetwork.gke.name

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = var.authorized_network
      display_name = "Authorized Network"
    }
  }

  release_channel {
    channel = "REGULAR"
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  addons_config {
    horizontal_pod_autoscaling {
      disabled = false
    }
    http_load_balancing {
      disabled = false
    }
    network_policy_config {
      disabled = false
    }
    gce_persistent_disk_csi_driver_config {
      enabled = true
    }
  }

  network_policy {
    enabled  = true
    provider = "CALICO"
  }

  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }

  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS"]
    managed_prometheus {
      enabled = true
    }
  }

  maintenance_policy {
    recurring_window {
      start_time = "2023-01-01T09:00:00Z"
      end_time   = "2023-01-01T17:00:00Z"
      recurrence = "FREQ=WEEKLY;BYDAY=SA,SU"
    }
  }

  resource_labels = {
    environment = var.environment
    project     = var.project
  }

  project = var.project_id
}
```

### Autopilot Cluster

```hcl
resource "google_container_cluster" "autopilot" {
  name     = "${var.project}-autopilot"
  location = var.region

  enable_autopilot = true

  network    = google_compute_network.main.name
  subnetwork = google_compute_subnetwork.gke.name

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  release_channel {
    channel = "REGULAR"
  }

  resource_labels = {
    environment = var.environment
    mode        = "autopilot"
  }

  project = var.project_id
}
```

## Node Pools

### Standard Node Pool

```hcl
resource "google_container_node_pool" "main" {
  name       = "${var.project}-node-pool"
  location   = var.region
  cluster    = google_container_cluster.main.name
  node_count = var.node_count

  node_config {
    machine_type = var.machine_type
    disk_size_gb = 100
    disk_type    = "pd-ssd"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    service_account = google_service_account.gke_node.email

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    metadata = {
      disable-legacy-endpoints = "true"
    }

    labels = {
      environment = var.environment
      node-pool   = "main"
    }

    tags = ["gke-node", var.project]
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
    strategy        = "SURGE"
  }

  project = var.project_id
}
```

### Autoscaling Node Pool

```hcl
resource "google_container_node_pool" "autoscaling" {
  name     = "${var.project}-autoscaling-pool"
  location = var.region
  cluster  = google_container_cluster.main.name

  autoscaling {
    min_node_count  = var.min_nodes
    max_node_count  = var.max_nodes
    location_policy = "BALANCED"
  }

  node_config {
    machine_type = var.machine_type
    disk_size_gb = 100
    disk_type    = "pd-ssd"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    service_account = google_service_account.gke_node.email

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    labels = {
      environment = var.environment
      node-pool   = "autoscaling"
    }
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  project = var.project_id
}
```

### Spot Node Pool

```hcl
resource "google_container_node_pool" "spot" {
  name     = "${var.project}-spot-pool"
  location = var.region
  cluster  = google_container_cluster.main.name

  autoscaling {
    min_node_count = 0
    max_node_count = 10
  }

  node_config {
    machine_type = var.machine_type
    spot         = true
    disk_size_gb = 100

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    service_account = google_service_account.gke_node.email

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    labels = {
      environment = var.environment
      node-pool   = "spot"
    }

    taint {
      key    = "cloud.google.com/gke-spot"
      value  = "true"
      effect = "NO_SCHEDULE"
    }
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  project = var.project_id
}
```

### GPU Node Pool

```hcl
resource "google_container_node_pool" "gpu" {
  name     = "${var.project}-gpu-pool"
  location = "${var.region}-a"  # Zonal for GPU
  cluster  = google_container_cluster.main.name

  autoscaling {
    min_node_count = 0
    max_node_count = 4
  }

  node_config {
    machine_type = "n1-standard-4"
    disk_size_gb = 100

    guest_accelerator {
      type  = "nvidia-tesla-t4"
      count = 1
      gpu_driver_installation_config {
        gpu_driver_version = "LATEST"
      }
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    service_account = google_service_account.gke_node.email

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    labels = {
      environment = var.environment
      node-pool   = "gpu"
    }

    taint {
      key    = "nvidia.com/gpu"
      value  = "present"
      effect = "NO_SCHEDULE"
    }
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  project = var.project_id
}
```

## Workload Identity

```hcl
# GKE Node Service Account
resource "google_service_account" "gke_node" {
  account_id   = "${var.project}-gke-node"
  display_name = "GKE Node Service Account"

  project = var.project_id
}

resource "google_project_iam_member" "gke_node_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gke_node.email}"
}

resource "google_project_iam_member" "gke_node_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.gke_node.email}"
}

resource "google_project_iam_member" "gke_node_viewer" {
  project = var.project_id
  role    = "roles/monitoring.viewer"
  member  = "serviceAccount:${google_service_account.gke_node.email}"
}

resource "google_project_iam_member" "gke_node_artifact_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.gke_node.email}"
}

# Workload Identity for application
resource "google_service_account" "app" {
  account_id   = "${var.project}-app"
  display_name = "Application Service Account"

  project = var.project_id
}

resource "google_service_account_iam_member" "workload_identity" {
  service_account_id = google_service_account.app.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${var.namespace}/${var.kubernetes_service_account}]"
}

# Grant permissions to app service account
resource "google_project_iam_member" "app_storage" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.app.email}"
}
```

## Binary Authorization

```hcl
resource "google_binary_authorization_policy" "main" {
  project = var.project_id

  default_admission_rule {
    evaluation_mode  = "REQUIRE_ATTESTATION"
    enforcement_mode = "ENFORCED_BLOCK_AND_AUDIT_LOG"
    require_attestations_by = [
      google_binary_authorization_attestor.main.name
    ]
  }

  cluster_admission_rules {
    cluster                 = "${var.region}.${google_container_cluster.main.name}"
    evaluation_mode         = "REQUIRE_ATTESTATION"
    enforcement_mode        = "ENFORCED_BLOCK_AND_AUDIT_LOG"
    require_attestations_by = [
      google_binary_authorization_attestor.main.name
    ]
  }
}

resource "google_binary_authorization_attestor" "main" {
  name    = "${var.project}-attestor"
  project = var.project_id

  attestation_authority_note {
    note_reference = google_container_analysis_note.main.name

    public_keys {
      id = data.google_kms_crypto_key_version.version.id
      pkix_public_key {
        public_key_pem      = data.google_kms_crypto_key_version.version.public_key[0].pem
        signature_algorithm = data.google_kms_crypto_key_version.version.public_key[0].algorithm
      }
    }
  }
}

resource "google_container_analysis_note" "main" {
  name    = "${var.project}-attestor-note"
  project = var.project_id

  attestation_authority {
    hint {
      human_readable_name = "Attestor Note"
    }
  }
}
```

## Config Connector

```hcl
resource "google_gke_hub_feature" "configmanagement" {
  name     = "configmanagement"
  location = "global"
  project  = var.project_id
}

resource "google_gke_hub_membership" "main" {
  membership_id = "${var.project}-membership"
  project       = var.project_id

  endpoint {
    gke_cluster {
      resource_link = google_container_cluster.main.id
    }
  }
}

resource "google_gke_hub_feature_membership" "configmanagement" {
  location   = "global"
  feature    = google_gke_hub_feature.configmanagement.name
  membership = google_gke_hub_membership.main.membership_id
  project    = var.project_id

  configmanagement {
    version = "1.15.0"

    config_sync {
      source_format = "hierarchy"

      git {
        sync_repo   = var.config_repo
        sync_branch = "main"
        policy_dir  = "config"
        secret_type = "ssh"
      }
    }

    policy_controller {
      enabled                    = true
      template_library_installed = true
      referential_rules_enabled  = true
    }
  }
}
```

## Kubernetes Provider Configuration

```hcl
data "google_client_config" "default" {}

provider "kubernetes" {
  host                   = "https://${google_container_cluster.main.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.main.master_auth[0].cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = "https://${google_container_cluster.main.endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(google_container_cluster.main.master_auth[0].cluster_ca_certificate)
  }
}
```

## Kubernetes Resources

### Namespace

```hcl
resource "kubernetes_namespace" "app" {
  metadata {
    name = var.namespace

    labels = {
      name        = var.namespace
      environment = var.environment
    }
  }

  depends_on = [google_container_node_pool.main]
}
```

### Service Account with Workload Identity

```hcl
resource "kubernetes_service_account" "app" {
  metadata {
    name      = var.kubernetes_service_account
    namespace = kubernetes_namespace.app.metadata[0].name

    annotations = {
      "iam.gke.io/gcp-service-account" = google_service_account.app.email
    }
  }
}
```

## Outputs

```hcl
output "cluster_id" {
  description = "GKE cluster ID"
  value       = google_container_cluster.main.id
}

output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.main.name
}

output "cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.main.endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = google_container_cluster.main.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "node_pool_name" {
  description = "Node pool name"
  value       = google_container_node_pool.main.name
}

output "gke_node_service_account" {
  description = "GKE node service account email"
  value       = google_service_account.gke_node.email
}

output "workload_identity_service_account" {
  description = "Workload identity service account email"
  value       = google_service_account.app.email
}

# kubectl configuration command
output "kubectl_config_command" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.main.name} --region ${var.region} --project ${var.project_id}"
}
```
