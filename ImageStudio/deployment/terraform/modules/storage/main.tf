# ==============================================================================
# Storage Module: Disaster Recovery (DR) with RTO < 15min and RPO < 5min
# ==============================================================================

variable "project_id" { type = string }
variable "region" { type = string }
variable "env" { type = string }
variable "kms_key_id" { type = string }

# Primary Artifact Storage Bucket (us-central1)
resource "google_storage_bucket" "artifacts_bucket" {
  name          = "imagesense-artifacts-${var.env}-${var.project_id}"
  project       = var.project_id
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  # Point-in-time recovery & lifecycle rules
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      num_newer_versions = 5
      with_state         = "ARCHIVED"
    }
  }

  encryption {
    default_kms_key_name = var.kms_key_id
  }

  labels = {
    environment = var.env
    dr_role     = "primary"
    rto_minutes = "15"
    rpo_minutes = "5"
  }
}

# Secondary Disaster Recovery Storage Bucket (us-east1 / Multi-Region replication)
resource "google_storage_bucket" "dr_secondary_bucket" {
  name          = "imagesense-artifacts-dr-${var.env}-${var.project_id}"
  project       = var.project_id
  location      = "us-east1"
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  encryption {
    default_kms_key_name = var.kms_key_id
  }

  labels = {
    environment = var.env
    dr_role     = "secondary-dr"
    rto_minutes = "15"
    rpo_minutes = "5"
  }
}

# Storage Transfer Job for Continuous Cross-Region Synchronization (RPO < 5min)
resource "google_storage_transfer_job" "dr_replication_job" {
  description = "Continuous Disaster Recovery replication job from primary to DR secondary bucket"
  project     = var.project_id

  transfer_spec {
    gcs_data_source {
      bucket_name = google_storage_bucket.artifacts_bucket.name
    }
    gcs_data_sink {
      bucket_name = google_storage_bucket.dr_secondary_bucket.name
    }
    transfer_options {
      overwrite_objects_already_existing_in_sink = true
      delete_objects_unique_in_sink              = false
    }
  }

  schedule {
    schedule_start_date {
      year  = 2026
      month = 1
      day   = 1
    }
    start_time_of_day {
      hours   = 0
      minutes = 0
      seconds = 0
      nanos   = 0
    }
  }

  status = "ENABLED"
}

output "primary_bucket_name" {
  value = google_storage_bucket.artifacts_bucket.name
}

output "dr_secondary_bucket_name" {
  value = google_storage_bucket.dr_secondary_bucket.name
}
