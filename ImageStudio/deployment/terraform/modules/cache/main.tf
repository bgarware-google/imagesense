# ==============================================================================
# Cache & State Module: Memorystore for Redis High Availability (HA) Mode
# ==============================================================================

variable "project_id" { type = string }
variable "region" { type = string }
variable "env" { type = string }

# Memorystore for Redis in STANDARD_HA (Multi-Zone Replication & <30s Automated Failover)
resource "google_redis_instance" "imagesense_redis_ha" {
  name           = "imagesense-redis-ha-${var.env}"
  project        = var.project_id
  region         = var.region
  tier           = "STANDARD_HA"
  memory_size_gb = var.env == "prod" ? 5 : 1

  # Primary node in zone a, Replica node in zone b for multi-zone redundancy
  location_id             = "${var.region}-a"
  alternative_location_id = "${var.region}-b"

  redis_version     = "REDIS_7_0"
  display_name      = "ImageSense Semantic Cache HA (${var.env})"
  transit_encryption_mode = "SERVER_AUTHENTICATION"

  # Automatic read replicas for high throughput
  read_replicas_mode = "READ_REPLICAS_ENABLED"
  replica_count      = 1

  # <30s automated failover maintenance policy
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 3
        minutes = 0
      }
    }
  }

  labels = {
    environment = var.env
    managed_by  = "terraform"
    ha_mode     = "standard_ha"
  }
}

# Vertex AI Search / Discovery Engine Data Store
resource "google_discovery_engine_data_store" "imagesense_datastore" {
  location                    = "global"
  data_store_id               = "imagesense-vector-cache-${var.env}"
  display_name                = "ImageSense Vector Datastore (${var.env})"
  industry_vertical           = "GENERIC"
  content_config              = "NO_CONTENT"
  solution_types              = ["SOLUTION_TYPE_SEARCH"]
  project                     = var.project_id
  create_advanced_site_search = false
}

output "redis_host" {
  value = google_redis_instance.imagesense_redis_ha.host
}

output "redis_port" {
  value = google_redis_instance.imagesense_redis_ha.port
}

output "datastore_id" {
  value = google_discovery_engine_data_store.imagesense_datastore.data_store_id
}
