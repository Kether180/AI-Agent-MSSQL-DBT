# DataMigrate AI - Local Docker Infrastructure
# Managed by Terraform for Infrastructure as Code

terraform {
  required_version = ">= 1.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

# Docker provider configuration
provider "docker" {
  # For Windows with Docker Desktop, uses named pipe by default
  # host = "npipe:////.//pipe//docker_engine"
}

# ============================================
# VARIABLES
# ============================================

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "postgres_user" {
  description = "PostgreSQL username"
  type        = string
  default     = "datamigrate"
}

variable "postgres_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
  default     = "datamigrate123"
}

variable "postgres_db" {
  description = "PostgreSQL database name"
  type        = string
  default     = "datamigrate"
}

variable "postgres_port" {
  description = "PostgreSQL exposed port"
  type        = number
  default     = 5432
}

variable "enable_monitoring" {
  description = "Enable Prometheus and Grafana monitoring"
  type        = bool
  default     = true
}

variable "prometheus_port" {
  description = "Prometheus exposed port"
  type        = number
  default     = 9090
}

variable "grafana_port" {
  description = "Grafana exposed port"
  type        = number
  default     = 3001
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  sensitive   = true
  default     = "datamigrate123"
}

# ============================================
# NETWORK
# ============================================

resource "docker_network" "datamigrate" {
  name   = "datamigrate-network-${var.environment}"
  driver = "bridge"
}

# ============================================
# VOLUMES (Persistent Storage)
# ============================================

resource "docker_volume" "postgres_data" {
  name = "datamigrate-pgdata-${var.environment}"
}

resource "docker_volume" "prometheus_data" {
  count = var.enable_monitoring ? 1 : 0
  name  = "datamigrate-prometheus-${var.environment}"
}

resource "docker_volume" "grafana_data" {
  count = var.enable_monitoring ? 1 : 0
  name  = "datamigrate-grafana-${var.environment}"
}

# ============================================
# POSTGRESQL WITH PGVECTOR
# ============================================

resource "docker_image" "postgres" {
  name         = "pgvector/pgvector:pg16"
  keep_locally = true
}

resource "docker_container" "postgres" {
  name  = "datamigrate-postgres-${var.environment}"
  image = docker_image.postgres.image_id

  restart = "unless-stopped"

  env = [
    "POSTGRES_USER=${var.postgres_user}",
    "POSTGRES_PASSWORD=${var.postgres_password}",
    "POSTGRES_DB=${var.postgres_db}",
  ]

  ports {
    internal = 5432
    external = var.postgres_port
  }

  volumes {
    volume_name    = docker_volume.postgres_data.name
    container_path = "/var/lib/postgresql/data"
  }

  networks_advanced {
    name = docker_network.datamigrate.name
  }

  healthcheck {
    test         = ["CMD-SHELL", "pg_isready -U ${var.postgres_user}"]
    interval     = "5s"
    timeout      = "5s"
    retries      = 5
    start_period = "10s"
  }

  # Wait for container to be healthy before considering it ready
  wait = true
  wait_timeout = 60
}

# ============================================
# PROMETHEUS (Metrics Collection)
# ============================================

resource "docker_image" "prometheus" {
  count        = var.enable_monitoring ? 1 : 0
  name         = "prom/prometheus:latest"
  keep_locally = true
}

resource "docker_container" "prometheus" {
  count = var.enable_monitoring ? 1 : 0
  name  = "datamigrate-prometheus-${var.environment}"
  image = docker_image.prometheus[0].image_id

  restart = "unless-stopped"

  ports {
    internal = 9090
    external = var.prometheus_port
  }

  volumes {
    volume_name    = docker_volume.prometheus_data[0].name
    container_path = "/prometheus"
  }

  # Mount prometheus config
  volumes {
    host_path      = abspath("${path.module}/prometheus.yml")
    container_path = "/etc/prometheus/prometheus.yml"
    read_only      = true
  }

  networks_advanced {
    name = docker_network.datamigrate.name
  }

  command = [
    "--config.file=/etc/prometheus/prometheus.yml",
    "--storage.tsdb.path=/prometheus",
    "--web.console.libraries=/usr/share/prometheus/console_libraries",
    "--web.console.templates=/usr/share/prometheus/consoles",
    "--web.enable-lifecycle"
  ]
}

# ============================================
# GRAFANA (Metrics Visualization)
# ============================================

resource "docker_image" "grafana" {
  count        = var.enable_monitoring ? 1 : 0
  name         = "grafana/grafana:latest"
  keep_locally = true
}

resource "docker_container" "grafana" {
  count = var.enable_monitoring ? 1 : 0
  name  = "datamigrate-grafana-${var.environment}"
  image = docker_image.grafana[0].image_id

  restart = "unless-stopped"

  env = [
    "GF_SECURITY_ADMIN_USER=admin",
    "GF_SECURITY_ADMIN_PASSWORD=${var.grafana_admin_password}",
    "GF_USERS_ALLOW_SIGN_UP=false",
    "GF_SERVER_ROOT_URL=http://localhost:${var.grafana_port}",
  ]

  ports {
    internal = 3000
    external = var.grafana_port
  }

  volumes {
    volume_name    = docker_volume.grafana_data[0].name
    container_path = "/var/lib/grafana"
  }

  # Mount datasource provisioning
  volumes {
    host_path      = abspath("${path.module}/grafana/provisioning")
    container_path = "/etc/grafana/provisioning"
    read_only      = true
  }

  networks_advanced {
    name = docker_network.datamigrate.name
  }

  depends_on = [docker_container.prometheus]
}

# ============================================
# OUTPUTS
# ============================================

output "postgres_container_id" {
  description = "PostgreSQL container ID"
  value       = docker_container.postgres.id
}

output "postgres_container_name" {
  description = "PostgreSQL container name"
  value       = docker_container.postgres.name
}

output "postgres_connection_string" {
  description = "PostgreSQL connection string (without password)"
  value       = "postgresql://${var.postgres_user}@localhost:${var.postgres_port}/${var.postgres_db}"
}

output "network_name" {
  description = "Docker network name"
  value       = docker_network.datamigrate.name
}

output "volume_name" {
  description = "PostgreSQL data volume name"
  value       = docker_volume.postgres_data.name
}

# Monitoring outputs (conditional)
output "prometheus_url" {
  description = "Prometheus URL"
  value       = var.enable_monitoring ? "http://localhost:${var.prometheus_port}" : "Monitoring disabled"
}

output "grafana_url" {
  description = "Grafana URL"
  value       = var.enable_monitoring ? "http://localhost:${var.grafana_port}" : "Monitoring disabled"
}

output "grafana_credentials" {
  description = "Grafana login credentials"
  value       = var.enable_monitoring ? "admin / [see grafana_admin_password variable]" : "Monitoring disabled"
}
