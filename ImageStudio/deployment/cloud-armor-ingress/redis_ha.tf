# ==============================================================================
# Memorystore for Redis High Availability (HA) & Multi-Zone Failover (<30s)
# ==============================================================================

resource "google_redis_instance" "redis_ha" {
  name           = "imagesense-redis-ha"
  project        = var.project_id
  region         = var.region
  tier           = "STANDARD_HA"
  memory_size_gb = 5

  # Primary node in zone a, Replica in zone b
  location_id             = "${var.region}-a"
  alternative_location_id = "${var.region}-b"

  redis_version           = "REDIS_7_0"
  display_name            = "ImageSense Redis Semantic Cache (High Availability)"
  transit_encryption_mode = "SERVER_AUTHENTICATION"

  read_replicas_mode = "READ_REPLICAS_ENABLED"
  replica_count      = 1

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
    ha_mode     = "standard_ha"
    failover    = "sub_30_seconds"
    managed_by  = "terraform"
  }
}

output "redis_ha_host" {
  description = "Memorystore for Redis HA Primary Host"
  value       = google_redis_instance.redis_ha.host
}

output "redis_ha_port" {
  description = "Memorystore for Redis HA Port"
  value       = google_redis_instance.redis_ha.port
}
