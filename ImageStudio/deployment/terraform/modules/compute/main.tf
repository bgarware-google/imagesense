# ==============================================================================
# Compute Module: Cloud Run Multi-Zone Redundancy & Warm Provisioning
# ==============================================================================

variable "project_id" { type = string }
variable "region" { type = string }
variable "env" { type = string }
variable "service_account" { type = string }

resource "google_cloud_run_v2_service" "imagesense_service" {
  name     = "image-studio-${var.env}"
  location = var.region
  project  = var.project_id

  # Ingress traffic controlled via Cloud Armor Load Balancer
  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = var.service_account

    containers {
      image = "gcr.io/${var.project_id}/imagesense-studio:${var.env}"

      resources {
        limits = {
          cpu    = "4"
          memory = "8Gi"
        }
        cpu_idle = false
      }

      env {
        name  = "ENVIRONMENT"
        value = var.env
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }

      # Health and Liveness Probes for automated zone-level failure eviction
      liveness_probe {
        http_get {
          path = "/api/v1/health"
          port = 8080
        }
        initial_delay_seconds = 10
        period_seconds        = 15
        failure_threshold     = 3
      }

      startup_probe {
        http_get {
          path = "/api/v1/health"
          port = 8080
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 5
      }
    }

    # Warm instance provisioning across 3 availability zones (us-central1-a, b, c)
    scaling {
      min_instance_count = var.env == "prod" ? 2 : 1
      max_instance_count = var.env == "prod" ? 20 : 5
    }

    max_instance_request_concurrency = 40
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Regional Serverless Network Endpoint Group (NEG) for cross-zone load balancing
resource "google_compute_region_network_endpoint_group" "serverless_neg" {
  name                  = "imagesense-neg-${var.env}"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  project               = var.project_id

  cloud_run {
    service = google_cloud_run_v2_service.imagesense_service.name
  }
}

output "service_uri" {
  value = google_cloud_run_v2_service.imagesense_service.uri
}

output "serverless_neg_id" {
  value = google_compute_region_network_endpoint_group.serverless_neg.id
}
