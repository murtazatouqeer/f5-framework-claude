# GCP Networking

## Overview

Google Cloud VPC provides global, scalable networking infrastructure. Terraform enables comprehensive configuration of VPCs, subnets, firewall rules, and connectivity.

## VPC Network

### Basic VPC

```hcl
resource "google_compute_network" "main" {
  name                    = "${var.project}-vpc"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"

  project = var.project_id
}
```

### Global VPC with Custom MTU

```hcl
resource "google_compute_network" "main" {
  name                            = "${var.project}-vpc"
  auto_create_subnetworks         = false
  routing_mode                    = "GLOBAL"
  mtu                             = 1460
  delete_default_routes_on_create = false

  project = var.project_id
}
```

## Subnets

### Basic Subnet

```hcl
resource "google_compute_subnetwork" "main" {
  name          = "${var.project}-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.main.id

  project = var.project_id
}
```

### Subnet with Secondary Ranges (for GKE)

```hcl
resource "google_compute_subnetwork" "gke" {
  name          = "${var.project}-gke-subnet"
  ip_cidr_range = "10.0.0.0/20"
  region        = var.region
  network       = google_compute_network.main.id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.1.0.0/16"
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.2.0.0/20"
  }

  private_ip_google_access = true

  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }

  project = var.project_id
}
```

### Multiple Subnets

```hcl
variable "subnets" {
  default = {
    "web" = {
      cidr   = "10.0.1.0/24"
      region = "us-central1"
    }
    "app" = {
      cidr   = "10.0.2.0/24"
      region = "us-central1"
    }
    "db" = {
      cidr   = "10.0.3.0/24"
      region = "us-central1"
    }
  }
}

resource "google_compute_subnetwork" "subnets" {
  for_each = var.subnets

  name          = "${var.project}-${each.key}-subnet"
  ip_cidr_range = each.value.cidr
  region        = each.value.region
  network       = google_compute_network.main.id

  private_ip_google_access = true

  project = var.project_id
}
```

## Firewall Rules

### Basic Rules

```hcl
# Allow internal traffic
resource "google_compute_firewall" "internal" {
  name    = "${var.project}-allow-internal"
  network = google_compute_network.main.name

  allow {
    protocol = "icmp"
  }

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  source_ranges = ["10.0.0.0/8"]

  project = var.project_id
}

# Allow SSH from IAP
resource "google_compute_firewall" "iap_ssh" {
  name    = "${var.project}-allow-iap-ssh"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"]  # IAP IP range

  target_tags = ["allow-ssh"]

  project = var.project_id
}

# Allow HTTP/HTTPS
resource "google_compute_firewall" "web" {
  name    = "${var.project}-allow-web"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["web"]

  project = var.project_id
}
```

### Firewall with Service Accounts

```hcl
resource "google_compute_firewall" "app_to_db" {
  name    = "${var.project}-app-to-db"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["5432"]
  }

  source_service_accounts = [google_service_account.app.email]
  target_service_accounts = [google_service_account.db.email]

  project = var.project_id
}
```

### Hierarchical Firewall Policies

```hcl
resource "google_compute_firewall_policy" "org_policy" {
  parent      = "organizations/${var.org_id}"
  short_name  = "org-firewall-policy"
  description = "Organization-wide firewall policy"
}

resource "google_compute_firewall_policy_rule" "deny_all_ingress" {
  firewall_policy = google_compute_firewall_policy.org_policy.id
  priority        = 9000
  action          = "deny"
  direction       = "INGRESS"
  description     = "Deny all ingress by default"

  match {
    layer4_configs {
      ip_protocol = "all"
    }
    src_ip_ranges = ["0.0.0.0/0"]
  }
}

resource "google_compute_firewall_policy_association" "org_association" {
  name              = "org-policy-association"
  firewall_policy   = google_compute_firewall_policy.org_policy.id
  attachment_target = "organizations/${var.org_id}"
}
```

## Cloud NAT

```hcl
resource "google_compute_router" "main" {
  name    = "${var.project}-router"
  region  = var.region
  network = google_compute_network.main.id

  bgp {
    asn = 64514
  }

  project = var.project_id
}

resource "google_compute_router_nat" "main" {
  name                               = "${var.project}-nat"
  router                             = google_compute_router.main.name
  region                             = google_compute_router.main.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }

  project = var.project_id
}
```

### NAT with Static IPs

```hcl
resource "google_compute_address" "nat" {
  count  = 2
  name   = "${var.project}-nat-ip-${count.index}"
  region = var.region

  project = var.project_id
}

resource "google_compute_router_nat" "main" {
  name                               = "${var.project}-nat"
  router                             = google_compute_router.main.name
  region                             = google_compute_router.main.region
  nat_ip_allocate_option             = "MANUAL_ONLY"
  nat_ips                            = google_compute_address.nat[*].self_link
  source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"

  subnetwork {
    name                    = google_compute_subnetwork.main.id
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"]
  }

  min_ports_per_vm                    = 64
  max_ports_per_vm                    = 65536
  enable_endpoint_independent_mapping = false

  log_config {
    enable = true
    filter = "ALL"
  }

  project = var.project_id
}
```

## Cloud VPN

### Classic VPN

```hcl
resource "google_compute_vpn_gateway" "main" {
  name    = "${var.project}-vpn-gateway"
  network = google_compute_network.main.id
  region  = var.region

  project = var.project_id
}

resource "google_compute_address" "vpn" {
  name   = "${var.project}-vpn-ip"
  region = var.region

  project = var.project_id
}

resource "google_compute_forwarding_rule" "esp" {
  name        = "${var.project}-vpn-esp"
  ip_protocol = "ESP"
  ip_address  = google_compute_address.vpn.address
  target      = google_compute_vpn_gateway.main.self_link
  region      = var.region

  project = var.project_id
}

resource "google_compute_forwarding_rule" "udp500" {
  name        = "${var.project}-vpn-udp500"
  ip_protocol = "UDP"
  port_range  = "500"
  ip_address  = google_compute_address.vpn.address
  target      = google_compute_vpn_gateway.main.self_link
  region      = var.region

  project = var.project_id
}

resource "google_compute_forwarding_rule" "udp4500" {
  name        = "${var.project}-vpn-udp4500"
  ip_protocol = "UDP"
  port_range  = "4500"
  ip_address  = google_compute_address.vpn.address
  target      = google_compute_vpn_gateway.main.self_link
  region      = var.region

  project = var.project_id
}

resource "google_compute_vpn_tunnel" "main" {
  name          = "${var.project}-vpn-tunnel"
  peer_ip       = var.peer_ip
  shared_secret = var.shared_secret

  target_vpn_gateway = google_compute_vpn_gateway.main.id

  local_traffic_selector  = ["10.0.0.0/16"]
  remote_traffic_selector = ["192.168.0.0/16"]

  depends_on = [
    google_compute_forwarding_rule.esp,
    google_compute_forwarding_rule.udp500,
    google_compute_forwarding_rule.udp4500,
  ]

  project = var.project_id
}
```

### HA VPN

```hcl
resource "google_compute_ha_vpn_gateway" "main" {
  name    = "${var.project}-ha-vpn"
  network = google_compute_network.main.id
  region  = var.region

  project = var.project_id
}

resource "google_compute_external_vpn_gateway" "peer" {
  name            = "${var.project}-peer-vpn"
  redundancy_type = "TWO_IPS_REDUNDANCY"

  interface {
    id         = 0
    ip_address = var.peer_ip_0
  }

  interface {
    id         = 1
    ip_address = var.peer_ip_1
  }

  project = var.project_id
}

resource "google_compute_vpn_tunnel" "tunnel0" {
  name                            = "${var.project}-tunnel-0"
  vpn_gateway                     = google_compute_ha_vpn_gateway.main.id
  peer_external_gateway           = google_compute_external_vpn_gateway.peer.id
  peer_external_gateway_interface = 0
  shared_secret                   = var.shared_secret
  router                          = google_compute_router.main.id
  vpn_gateway_interface           = 0

  project = var.project_id
}

resource "google_compute_vpn_tunnel" "tunnel1" {
  name                            = "${var.project}-tunnel-1"
  vpn_gateway                     = google_compute_ha_vpn_gateway.main.id
  peer_external_gateway           = google_compute_external_vpn_gateway.peer.id
  peer_external_gateway_interface = 1
  shared_secret                   = var.shared_secret
  router                          = google_compute_router.main.id
  vpn_gateway_interface           = 1

  project = var.project_id
}

resource "google_compute_router_interface" "tunnel0" {
  name       = "${var.project}-interface-0"
  router     = google_compute_router.main.name
  region     = var.region
  ip_range   = "169.254.0.1/30"
  vpn_tunnel = google_compute_vpn_tunnel.tunnel0.name

  project = var.project_id
}

resource "google_compute_router_peer" "tunnel0" {
  name                      = "${var.project}-peer-0"
  router                    = google_compute_router.main.name
  region                    = var.region
  peer_ip_address           = "169.254.0.2"
  peer_asn                  = var.peer_asn
  advertised_route_priority = 100
  interface                 = google_compute_router_interface.tunnel0.name

  project = var.project_id
}
```

## Private Service Connect

```hcl
# Reserve internal address for PSC
resource "google_compute_global_address" "psc" {
  name          = "${var.project}-psc-address"
  purpose       = "PRIVATE_SERVICE_CONNECT"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id

  project = var.project_id
}

# Private connection to Google services
resource "google_service_networking_connection" "main" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.psc.name]
}
```

## Shared VPC

### Host Project

```hcl
resource "google_compute_shared_vpc_host_project" "host" {
  project = var.host_project_id
}
```

### Service Project

```hcl
resource "google_compute_shared_vpc_service_project" "service" {
  host_project    = google_compute_shared_vpc_host_project.host.project
  service_project = var.service_project_id
}
```

## Load Balancer

### Global HTTP(S) Load Balancer

```hcl
# Backend service
resource "google_compute_backend_service" "main" {
  name        = "${var.project}-backend"
  port_name   = "http"
  protocol    = "HTTP"
  timeout_sec = 30

  health_checks = [google_compute_health_check.http.id]

  backend {
    group           = google_compute_instance_group_manager.main.instance_group
    balancing_mode  = "UTILIZATION"
    capacity_scaler = 1.0
  }

  project = var.project_id
}

# Health check
resource "google_compute_health_check" "http" {
  name               = "${var.project}-health-check"
  check_interval_sec = 5
  timeout_sec        = 5

  http_health_check {
    port         = 80
    request_path = "/health"
  }

  project = var.project_id
}

# URL map
resource "google_compute_url_map" "main" {
  name            = "${var.project}-url-map"
  default_service = google_compute_backend_service.main.id

  project = var.project_id
}

# HTTPS proxy
resource "google_compute_target_https_proxy" "main" {
  name             = "${var.project}-https-proxy"
  url_map          = google_compute_url_map.main.id
  ssl_certificates = [google_compute_managed_ssl_certificate.main.id]

  project = var.project_id
}

# SSL certificate
resource "google_compute_managed_ssl_certificate" "main" {
  name = "${var.project}-cert"

  managed {
    domains = [var.domain_name]
  }

  project = var.project_id
}

# Global forwarding rule
resource "google_compute_global_forwarding_rule" "https" {
  name       = "${var.project}-https-rule"
  target     = google_compute_target_https_proxy.main.id
  port_range = "443"
  ip_address = google_compute_global_address.lb.address

  project = var.project_id
}

# Static IP
resource "google_compute_global_address" "lb" {
  name = "${var.project}-lb-ip"

  project = var.project_id
}
```

## Outputs

```hcl
output "network_id" {
  description = "VPC network ID"
  value       = google_compute_network.main.id
}

output "network_name" {
  description = "VPC network name"
  value       = google_compute_network.main.name
}

output "network_self_link" {
  description = "VPC network self link"
  value       = google_compute_network.main.self_link
}

output "subnet_ids" {
  description = "Subnet IDs"
  value       = { for k, v in google_compute_subnetwork.subnets : k => v.id }
}

output "nat_ip" {
  description = "NAT IP address"
  value       = google_compute_router_nat.main.nat_ips
}
```
