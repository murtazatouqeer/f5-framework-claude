# Azure AKS (Azure Kubernetes Service)

## Overview

Azure Kubernetes Service provides managed Kubernetes clusters. Terraform enables comprehensive AKS configuration including node pools, networking, and identity management.

## AKS Cluster

### Basic Cluster

```hcl
resource "azurerm_kubernetes_cluster" "main" {
  name                = "${var.project}-aks"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = var.project

  default_node_pool {
    name       = "default"
    node_count = 2
    vm_size    = "Standard_D2s_v3"
  }

  identity {
    type = "SystemAssigned"
  }

  tags = {
    Environment = var.environment
  }
}
```

### Production Cluster

```hcl
resource "azurerm_kubernetes_cluster" "main" {
  name                = "${var.project}-aks"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = var.project
  kubernetes_version  = var.kubernetes_version

  default_node_pool {
    name                 = "system"
    node_count           = 3
    vm_size              = "Standard_D4s_v3"
    vnet_subnet_id       = azurerm_subnet.aks.id
    os_disk_size_gb      = 128
    os_disk_type         = "Managed"
    type                 = "VirtualMachineScaleSets"
    enable_auto_scaling  = true
    min_count            = 3
    max_count            = 5
    max_pods             = 110
    zones                = ["1", "2", "3"]

    node_labels = {
      "nodepool-type" = "system"
      "environment"   = var.environment
    }

    upgrade_settings {
      max_surge = "33%"
    }
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aks.id]
  }

  kubelet_identity {
    client_id                 = azurerm_user_assigned_identity.kubelet.client_id
    object_id                 = azurerm_user_assigned_identity.kubelet.principal_id
    user_assigned_identity_id = azurerm_user_assigned_identity.kubelet.id
  }

  network_profile {
    network_plugin     = "azure"
    network_policy     = "calico"
    dns_service_ip     = "10.2.0.10"
    service_cidr       = "10.2.0.0/16"
    load_balancer_sku  = "standard"
    outbound_type      = "loadBalancer"
  }

  private_cluster_enabled = true
  private_dns_zone_id     = azurerm_private_dns_zone.aks.id

  api_server_access_profile {
    authorized_ip_ranges = var.authorized_ip_ranges
  }

  azure_active_directory_role_based_access_control {
    managed                = true
    azure_rbac_enabled     = true
    admin_group_object_ids = var.admin_group_ids
  }

  oidc_issuer_enabled       = true
  workload_identity_enabled = true

  key_vault_secrets_provider {
    secret_rotation_enabled  = true
    secret_rotation_interval = "2m"
  }

  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  }

  microsoft_defender {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  }

  maintenance_window {
    allowed {
      day   = "Saturday"
      hours = [1, 2, 3, 4]
    }
    allowed {
      day   = "Sunday"
      hours = [1, 2, 3, 4]
    }
  }

  auto_scaler_profile {
    balance_similar_node_groups      = true
    expander                         = "random"
    max_graceful_termination_sec     = 600
    max_node_provisioning_time       = "15m"
    max_unready_nodes                = 3
    max_unready_percentage           = 45
    new_pod_scale_up_delay           = "10s"
    scale_down_delay_after_add       = "10m"
    scale_down_delay_after_delete    = "10s"
    scale_down_delay_after_failure   = "3m"
    scan_interval                    = "10s"
    scale_down_unneeded              = "10m"
    scale_down_unready               = "20m"
    scale_down_utilization_threshold = 0.5
    skip_nodes_with_local_storage    = false
    skip_nodes_with_system_pods      = true
  }

  tags = {
    Environment = var.environment
    Project     = var.project
  }

  lifecycle {
    ignore_changes = [
      default_node_pool[0].node_count,
      kubernetes_version
    ]
  }
}
```

## Node Pools

### User Node Pool

```hcl
resource "azurerm_kubernetes_cluster_node_pool" "user" {
  name                  = "user"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = "Standard_D4s_v3"
  node_count            = 3
  vnet_subnet_id        = azurerm_subnet.aks.id
  os_disk_size_gb       = 128
  os_disk_type          = "Managed"
  enable_auto_scaling   = true
  min_count             = 2
  max_count             = 10
  max_pods              = 110
  zones                 = ["1", "2", "3"]

  node_labels = {
    "nodepool-type" = "user"
    "environment"   = var.environment
  }

  node_taints = []

  upgrade_settings {
    max_surge = "33%"
  }

  tags = {
    Environment = var.environment
  }
}
```

### Spot Node Pool

```hcl
resource "azurerm_kubernetes_cluster_node_pool" "spot" {
  name                  = "spot"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = "Standard_D4s_v3"
  vnet_subnet_id        = azurerm_subnet.aks.id
  os_disk_size_gb       = 128
  enable_auto_scaling   = true
  min_count             = 0
  max_count             = 10
  priority              = "Spot"
  eviction_policy       = "Delete"
  spot_max_price        = -1

  node_labels = {
    "kubernetes.azure.com/scalesetpriority" = "spot"
  }

  node_taints = [
    "kubernetes.azure.com/scalesetpriority=spot:NoSchedule"
  ]

  tags = {
    Environment = var.environment
    SpotInstance = "true"
  }
}
```

### GPU Node Pool

```hcl
resource "azurerm_kubernetes_cluster_node_pool" "gpu" {
  name                  = "gpu"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = "Standard_NC6s_v3"
  vnet_subnet_id        = azurerm_subnet.aks.id
  os_disk_size_gb       = 256
  enable_auto_scaling   = true
  min_count             = 0
  max_count             = 4
  zones                 = ["1"]

  node_labels = {
    "accelerator" = "nvidia"
  }

  node_taints = [
    "nvidia.com/gpu=present:NoSchedule"
  ]

  tags = {
    Environment = var.environment
    GPU         = "true"
  }
}
```

## Identity and Access

### User Assigned Identity

```hcl
resource "azurerm_user_assigned_identity" "aks" {
  name                = "${var.project}-aks-identity"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
}

resource "azurerm_user_assigned_identity" "kubelet" {
  name                = "${var.project}-kubelet-identity"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
}

# Role assignments for AKS identity
resource "azurerm_role_assignment" "aks_network_contributor" {
  scope                = azurerm_virtual_network.main.id
  role_definition_name = "Network Contributor"
  principal_id         = azurerm_user_assigned_identity.aks.principal_id
}

resource "azurerm_role_assignment" "aks_private_dns_contributor" {
  scope                = azurerm_private_dns_zone.aks.id
  role_definition_name = "Private DNS Zone Contributor"
  principal_id         = azurerm_user_assigned_identity.aks.principal_id
}

# Role assignments for Kubelet identity
resource "azurerm_role_assignment" "kubelet_acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.kubelet.principal_id
}
```

### Workload Identity

```hcl
resource "azurerm_user_assigned_identity" "app" {
  name                = "${var.project}-app-identity"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
}

resource "azurerm_federated_identity_credential" "app" {
  name                = "${var.project}-app-federated"
  resource_group_name = azurerm_resource_group.main.name
  parent_id           = azurerm_user_assigned_identity.app.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = azurerm_kubernetes_cluster.main.oidc_issuer_url
  subject             = "system:serviceaccount:${var.namespace}:${var.service_account_name}"
}

resource "azurerm_role_assignment" "app_keyvault" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}

resource "azurerm_role_assignment" "app_storage" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}
```

## Private DNS Zone

```hcl
resource "azurerm_private_dns_zone" "aks" {
  name                = "privatelink.${var.location}.azmk8s.io"
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "aks" {
  name                  = "${var.project}-aks-dns-link"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.aks.name
  virtual_network_id    = azurerm_virtual_network.main.id
  registration_enabled  = false
}
```

## Container Registry

```hcl
resource "azurerm_container_registry" "main" {
  name                = "${replace(var.project, "-", "")}acr"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Premium"
  admin_enabled       = false

  network_rule_set {
    default_action = "Deny"

    virtual_network {
      action    = "Allow"
      subnet_id = azurerm_subnet.aks.id
    }
  }

  georeplications {
    location                = "West Europe"
    zone_redundancy_enabled = true
  }

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_private_endpoint" "acr" {
  name                = "${var.project}-acr-pe"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.endpoints.id

  private_service_connection {
    name                           = "acr-connection"
    private_connection_resource_id = azurerm_container_registry.main.id
    is_manual_connection           = false
    subresource_names              = ["registry"]
  }

  private_dns_zone_group {
    name                 = "acr-dns-zone-group"
    private_dns_zone_ids = [azurerm_private_dns_zone.acr.id]
  }
}
```

## Log Analytics

```hcl
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.project}-law"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_log_analytics_solution" "containers" {
  solution_name         = "ContainerInsights"
  location              = azurerm_resource_group.main.location
  resource_group_name   = azurerm_resource_group.main.name
  workspace_resource_id = azurerm_log_analytics_workspace.main.id
  workspace_name        = azurerm_log_analytics_workspace.main.name

  plan {
    publisher = "Microsoft"
    product   = "OMSGallery/ContainerInsights"
  }
}
```

## Kubernetes Provider Configuration

```hcl
provider "kubernetes" {
  host                   = azurerm_kubernetes_cluster.main.kube_config[0].host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.main.kube_config[0].client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.main.kube_config[0].client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.main.kube_config[0].cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = azurerm_kubernetes_cluster.main.kube_config[0].host
    client_certificate     = base64decode(azurerm_kubernetes_cluster.main.kube_config[0].client_certificate)
    client_key             = base64decode(azurerm_kubernetes_cluster.main.kube_config[0].client_key)
    cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.main.kube_config[0].cluster_ca_certificate)
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

  depends_on = [azurerm_kubernetes_cluster.main]
}
```

### Service Account with Workload Identity

```hcl
resource "kubernetes_service_account" "app" {
  metadata {
    name      = var.service_account_name
    namespace = kubernetes_namespace.app.metadata[0].name

    annotations = {
      "azure.workload.identity/client-id" = azurerm_user_assigned_identity.app.client_id
    }

    labels = {
      "azure.workload.identity/use" = "true"
    }
  }
}
```

## Outputs

```hcl
output "cluster_id" {
  description = "AKS cluster ID"
  value       = azurerm_kubernetes_cluster.main.id
}

output "cluster_name" {
  description = "AKS cluster name"
  value       = azurerm_kubernetes_cluster.main.name
}

output "cluster_fqdn" {
  description = "AKS cluster FQDN"
  value       = azurerm_kubernetes_cluster.main.fqdn
}

output "kube_config" {
  description = "Kubernetes config"
  value       = azurerm_kubernetes_cluster.main.kube_config_raw
  sensitive   = true
}

output "oidc_issuer_url" {
  description = "OIDC issuer URL for workload identity"
  value       = azurerm_kubernetes_cluster.main.oidc_issuer_url
}

output "node_resource_group" {
  description = "AKS node resource group"
  value       = azurerm_kubernetes_cluster.main.node_resource_group
}

output "kubelet_identity_client_id" {
  description = "Kubelet identity client ID"
  value       = azurerm_user_assigned_identity.kubelet.client_id
}

output "acr_login_server" {
  description = "ACR login server"
  value       = azurerm_container_registry.main.login_server
}

# kubectl configuration command
output "kubectl_config_command" {
  description = "Command to configure kubectl"
  value       = "az aks get-credentials --resource-group ${azurerm_resource_group.main.name} --name ${azurerm_kubernetes_cluster.main.name}"
}
```
