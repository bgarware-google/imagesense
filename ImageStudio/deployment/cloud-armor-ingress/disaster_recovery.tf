# ==============================================================================
# Disaster Recovery (DR) Infrastructure: RTO < 15min, RPO < 5min
# ==============================================================================

# Secondary Disaster Recovery Storage Bucket (us-east1)
resource "google_storage_bucket" "dr_secondary_bucket" {
  name          = "imagesense-artifacts-dr-${var.project_id}"
  project       = var.project_id
  location      = "us-east1"
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.gcs_key.id
  }

  labels = {
    dr_tier     = "secondary"
    rto_target  = "15m"
    rpo_target  = "5m"
    managed_by  = "terraform"
  }
}

# Continuous Storage Transfer Replication Job (RPO < 5min)
resource "google_storage_transfer_job" "dr_sync_job" {
  description = "Cross-Region Disaster Recovery Replication (us-central1 -> us-east1)"
  project     = var.project_id

  transfer_spec {
    gcs_data_source {
      bucket_name = google_storage_bucket.image_artifacts.name
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

output "dr_secondary_bucket_name" {
  description = "Secondary Disaster Recovery Bucket Name"
  value       = google_storage_bucket.dr_secondary_bucket.name
}
