variable "project_id" { type = string }
variable "env" { type = string }

resource "google_service_account" "api_sa" {
  account_id   = "sa-imagesense-api-${var.env}"
  display_name = "ImageSense Ingress API Service Account (${var.env})"
  project      = var.project_id
}

resource "google_service_account" "worker_sa" {
  account_id   = "sa-imagesense-worker-${var.env}"
  display_name = "ImageSense Worker Service Account (${var.env})"
  project      = var.project_id
}

resource "google_project_iam_member" "api_vertex" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_project_iam_member" "api_storage" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

output "api_service_account_email" {
  value = google_service_account.api_sa.email
}

output "worker_service_account_email" {
  value = google_service_account.worker_sa.email
}
