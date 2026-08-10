variable "project_id" { type = string }
variable "region" { type = string }
variable "env" { type = string }
variable "kms_key_id" { type = string }

resource "google_storage_bucket" "artifacts_bucket" {
  name          = "imagesense-artifacts-${var.env}-${var.project_id}"
  project       = var.project_id
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  encryption {
    default_kms_key_name = var.kms_key_id
  }
}

output "bucket_name" {
  value = google_storage_bucket.artifacts_bucket.name
}
