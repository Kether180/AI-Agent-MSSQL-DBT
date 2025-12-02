# DataMigrate AI - Local Development Variables
# Passwords are read from Windows Environment Variables (TF_VAR_*)

environment       = "dev"
postgres_user     = "datamigrate"
postgres_db       = "datamigrate"
postgres_port     = 5432

# Monitoring (Prometheus + Grafana)
enable_monitoring = true
prometheus_port   = 9090
grafana_port      = 3001

# PASSWORDS: Set these Windows Environment Variables:
# TF_VAR_postgres_password
# TF_VAR_grafana_admin_password
