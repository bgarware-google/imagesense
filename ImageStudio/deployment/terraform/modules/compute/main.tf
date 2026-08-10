variable "project_id" { type = string }
variable "region" { type = string }
variable "env" { type = string }
variable "service_account" { type = string }

resource "google_cloud_run_v2_service" "imagesense_service" {
  name     = "image-studio-${var.env}"
  location = var.region
  project  = var.project_id

  template {
    service_account = var.service_account
    containers {
      image = "gcr.io/${var.project_id}/imagesense-studio:${var.env}"
      resources {
        limits = {
          cpu    = "4"
          memory = "8Gi"
        }
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
    }
    scaling {
      min_instance_count = var.env == "prod" ? 1 : 0
      max_instance_count = var.env == "prod" ? 10 : 3
    }
  }
}

output "service_uri" {
  value = google_cloud_run_v2_service.imagesense_service.uri
}
