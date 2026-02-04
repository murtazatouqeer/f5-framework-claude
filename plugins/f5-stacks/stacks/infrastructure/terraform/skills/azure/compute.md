# Azure Compute

## Overview

Azure provides various compute options including Virtual Machines, Scale Sets, and Container Instances. Terraform enables comprehensive configuration of these resources.

## Virtual Machine

### Basic Linux VM

```hcl
resource "azurerm_linux_virtual_machine" "main" {
  name                = "${var.project}-vm"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  size                = "Standard_B2s"
  admin_username      = var.admin_username

  network_interface_ids = [
    azurerm_network_interface.main.id
  ]

  admin_ssh_key {
    username   = var.admin_username
    public_key = file("~/.ssh/id_rsa.pub")
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts"
    version   = "latest"
  }

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_network_interface" "main" {
  name                = "${var.project}-nic"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.main.id
    private_ip_address_allocation = "Dynamic"
  }

  tags = {
    Environment = var.environment
  }
}
```

### Production Linux VM

```hcl
resource "azurerm_linux_virtual_machine" "main" {
  name                  = "${var.project}-vm"
  resource_group_name   = azurerm_resource_group.main.name
  location              = azurerm_resource_group.main.location
  size                  = var.vm_size
  admin_username        = var.admin_username
  availability_set_id   = azurerm_availability_set.main.id
  zone                  = "1"

  network_interface_ids = [
    azurerm_network_interface.main.id
  ]

  admin_ssh_key {
    username   = var.admin_username
    public_key = file(var.ssh_public_key_path)
  }

  os_disk {
    name                 = "${var.project}-osdisk"
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
    disk_size_gb         = 64
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.vm.id]
  }

  boot_diagnostics {
    storage_account_uri = azurerm_storage_account.diagnostics.primary_blob_endpoint
  }

  custom_data = base64encode(file("${path.module}/cloud-init.yaml"))

  encryption_at_host_enabled = true

  tags = {
    Environment = var.environment
    Project     = var.project
  }

  lifecycle {
    ignore_changes = [
      custom_data
    ]
  }
}

# Managed disk
resource "azurerm_managed_disk" "data" {
  name                 = "${var.project}-datadisk"
  location             = azurerm_resource_group.main.location
  resource_group_name  = azurerm_resource_group.main.name
  storage_account_type = "Premium_LRS"
  create_option        = "Empty"
  disk_size_gb         = 256
  zone                 = "1"

  encryption_settings {
    enabled = true
  }

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_virtual_machine_data_disk_attachment" "data" {
  managed_disk_id    = azurerm_managed_disk.data.id
  virtual_machine_id = azurerm_linux_virtual_machine.main.id
  lun                = 0
  caching            = "ReadWrite"
}
```

### Windows VM

```hcl
resource "azurerm_windows_virtual_machine" "main" {
  name                = "${var.project}-win-vm"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  size                = var.vm_size
  admin_username      = var.admin_username
  admin_password      = var.admin_password

  network_interface_ids = [
    azurerm_network_interface.windows.id
  ]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
  }

  source_image_reference {
    publisher = "MicrosoftWindowsServer"
    offer     = "WindowsServer"
    sku       = "2022-Datacenter"
    version   = "latest"
  }

  winrm_listener {
    protocol = "Https"
  }

  enable_automatic_updates = true
  patch_mode               = "AutomaticByPlatform"
  hotpatching_enabled      = true

  tags = {
    Environment = var.environment
  }
}
```

## Virtual Machine Scale Set

### Linux VMSS

```hcl
resource "azurerm_linux_virtual_machine_scale_set" "main" {
  name                = "${var.project}-vmss"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.vm_size
  instances           = var.instance_count
  admin_username      = var.admin_username

  admin_ssh_key {
    username   = var.admin_username
    public_key = file(var.ssh_public_key_path)
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  os_disk {
    storage_account_type = "Premium_LRS"
    caching              = "ReadWrite"
  }

  network_interface {
    name    = "${var.project}-nic"
    primary = true

    ip_configuration {
      name                                   = "internal"
      primary                                = true
      subnet_id                              = azurerm_subnet.main.id
      load_balancer_backend_address_pool_ids = [azurerm_lb_backend_address_pool.main.id]
    }
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.vmss.id]
  }

  boot_diagnostics {
    storage_account_uri = azurerm_storage_account.diagnostics.primary_blob_endpoint
  }

  health_probe_id = azurerm_lb_probe.http.id

  upgrade_mode = "Rolling"

  rolling_upgrade_policy {
    max_batch_instance_percent              = 20
    max_unhealthy_instance_percent          = 20
    max_unhealthy_upgraded_instance_percent = 5
    pause_time_between_batches              = "PT0S"
  }

  automatic_os_upgrade_policy {
    disable_automatic_rollback  = false
    enable_automatic_os_upgrade = true
  }

  automatic_instance_repair {
    enabled      = true
    grace_period = "PT30M"
  }

  zones = ["1", "2", "3"]

  tags = {
    Environment = var.environment
  }
}
```

### VMSS with Spot Instances

```hcl
resource "azurerm_linux_virtual_machine_scale_set" "spot" {
  name                = "${var.project}-spot-vmss"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.vm_size
  instances           = var.spot_instance_count
  admin_username      = var.admin_username

  priority        = "Spot"
  eviction_policy = "Deallocate"
  max_bid_price   = -1  # Pay up to on-demand price

  admin_ssh_key {
    username   = var.admin_username
    public_key = file(var.ssh_public_key_path)
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  os_disk {
    storage_account_type = "Standard_LRS"
    caching              = "ReadWrite"
  }

  network_interface {
    name    = "${var.project}-spot-nic"
    primary = true

    ip_configuration {
      name      = "internal"
      primary   = true
      subnet_id = azurerm_subnet.main.id
    }
  }

  tags = {
    Environment = var.environment
    SpotInstance = "true"
  }
}
```

## Autoscaling

### VMSS Autoscale

```hcl
resource "azurerm_monitor_autoscale_setting" "main" {
  name                = "${var.project}-autoscale"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  target_resource_id  = azurerm_linux_virtual_machine_scale_set.main.id

  profile {
    name = "default"

    capacity {
      default = var.default_instance_count
      minimum = var.min_instance_count
      maximum = var.max_instance_count
    }

    rule {
      metric_trigger {
        metric_name        = "Percentage CPU"
        metric_resource_id = azurerm_linux_virtual_machine_scale_set.main.id
        time_grain         = "PT1M"
        statistic          = "Average"
        time_window        = "PT5M"
        time_aggregation   = "Average"
        operator           = "GreaterThan"
        threshold          = 75
      }

      scale_action {
        direction = "Increase"
        type      = "ChangeCount"
        value     = "2"
        cooldown  = "PT1M"
      }
    }

    rule {
      metric_trigger {
        metric_name        = "Percentage CPU"
        metric_resource_id = azurerm_linux_virtual_machine_scale_set.main.id
        time_grain         = "PT1M"
        statistic          = "Average"
        time_window        = "PT5M"
        time_aggregation   = "Average"
        operator           = "LessThan"
        threshold          = 25
      }

      scale_action {
        direction = "Decrease"
        type      = "ChangeCount"
        value     = "1"
        cooldown  = "PT1M"
      }
    }
  }

  notification {
    email {
      send_to_subscription_administrator    = true
      send_to_subscription_co_administrator = true
      custom_emails                         = var.alert_emails
    }
  }
}
```

## Availability Set

```hcl
resource "azurerm_availability_set" "main" {
  name                         = "${var.project}-avset"
  location                     = azurerm_resource_group.main.location
  resource_group_name          = azurerm_resource_group.main.name
  platform_fault_domain_count  = 2
  platform_update_domain_count = 5
  managed                      = true

  tags = {
    Environment = var.environment
  }
}
```

## Managed Identity

```hcl
resource "azurerm_user_assigned_identity" "vm" {
  name                = "${var.project}-vm-identity"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
}

resource "azurerm_role_assignment" "vm_storage" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_user_assigned_identity.vm.principal_id
}

resource "azurerm_role_assignment" "vm_keyvault" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.vm.principal_id
}
```

## Container Instances

```hcl
resource "azurerm_container_group" "main" {
  name                = "${var.project}-container"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  ip_address_type     = "Private"
  os_type             = "Linux"
  subnet_ids          = [azurerm_subnet.containers.id]

  container {
    name   = "app"
    image  = "${azurerm_container_registry.main.login_server}/${var.image_name}:${var.image_tag}"
    cpu    = "1"
    memory = "2"

    ports {
      port     = 8080
      protocol = "TCP"
    }

    environment_variables = {
      ENV = var.environment
    }

    secure_environment_variables = {
      DATABASE_URL = var.database_url
    }

    liveness_probe {
      http_get {
        path   = "/health"
        port   = 8080
        scheme = "Http"
      }
      initial_delay_seconds = 30
      period_seconds        = 10
      failure_threshold     = 3
    }
  }

  image_registry_credential {
    server   = azurerm_container_registry.main.login_server
    username = azurerm_container_registry.main.admin_username
    password = azurerm_container_registry.main.admin_password
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.container.id]
  }

  tags = {
    Environment = var.environment
  }
}
```

## Proximity Placement Groups

```hcl
resource "azurerm_proximity_placement_group" "main" {
  name                = "${var.project}-ppg"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_linux_virtual_machine" "low_latency" {
  name                       = "${var.project}-low-latency-vm"
  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  size                       = "Standard_D4s_v3"
  admin_username             = var.admin_username
  proximity_placement_group_id = azurerm_proximity_placement_group.main.id

  network_interface_ids = [
    azurerm_network_interface.low_latency.id
  ]

  admin_ssh_key {
    username   = var.admin_username
    public_key = file(var.ssh_public_key_path)
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }
}
```

## Outputs

```hcl
output "vm_id" {
  description = "Virtual machine ID"
  value       = azurerm_linux_virtual_machine.main.id
}

output "vm_private_ip" {
  description = "Virtual machine private IP"
  value       = azurerm_network_interface.main.private_ip_address
}

output "vmss_id" {
  description = "VMSS ID"
  value       = azurerm_linux_virtual_machine_scale_set.main.id
}

output "vmss_identity_principal_id" {
  description = "VMSS managed identity principal ID"
  value       = azurerm_user_assigned_identity.vmss.principal_id
}

output "container_group_ip" {
  description = "Container group IP"
  value       = azurerm_container_group.main.ip_address
}
```
