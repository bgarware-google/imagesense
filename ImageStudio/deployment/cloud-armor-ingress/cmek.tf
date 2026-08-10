# ==============================================================================
# Cloud KMS CMEK (Customer-Managed Encryption Keys) & Persistent Storage Layers
# ==============================================================================

# -----------------------------------------------------------------------------
# 1. Cloud KMS Key Ring & CMEK Crypto Keys with Automated Rotation
# -----------------------------------------------------------------------------
resource "google_kms_key_ring" "imagesense_keyring" {
  name     = "imagesense-keyring"
  location = var.region
  project  = var.project_id
}

# GCS Artifacts CMEK Key (Rotates every 90 days = 7776000s)
resource "google_kms_crypto_key" "gcs_key" {
  name            = "imagesense-gcs-cmek-key"
  key_ring        = google_kms_key_ring.imagesense_keyring.id
  rotation_period = "7776000s"

  lifecycle {
    prevent_destroy = false
  }
}

# BigQuery Telemetry CMEK Key
resource "google_kms_crypto_key" "bq_key" {
  name            = "imagesense-bq-cmek-key"
  key_ring        = google_kms_key_ring.imagesense_keyring.id
  rotation_period = "7776000s"

  lifecycle {
    prevent_destroy = false
  }
}

# Vertex AI / Vector Search CMEK Key
resource "google_kms_crypto_key" "vertex_key" {
  name            = "imagesense-vertex-cmek-key"
  key_ring        = google_kms_key_ring.imagesense_keyring.id
  rotation_period = "7776000s"

  lifecycle {
    prevent_destroy = false
  }
}

# -----------------------------------------------------------------------------
# 2. CMEK-Encrypted Persistent Storage Layers
# -----------------------------------------------------------------------------

# GCS Image Artifacts Bucket with Default CMEK
resource "google_storage_bucket" "artifact_bucket" {
  name                        = "imagesense-artifacts-${var.project_id}"
  location                    = var.region
  project                     = var.project_id
  force_destroy               = true
  uniform_bucket_level_access = true

  encryption {
    default_kms_key_name = google_kms_crypto_key.gcs_key.id
  }

  versioning {
    enabled = true
  }
}

# BigQuery Telemetry Dataset with Default CMEK
resource "google_bigquery_dataset" "telemetry_dataset" {
  dataset_id  = "imagesense_telemetry"
  description = "ImageSense analytical and telemetry dataset protected with CMEK"
  location    = var.region
  project     = var.project_id

  default_encryption_configuration {
    kms_key_name = google_kms_crypto_key.bq_key.id
  }
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "kms_keyring_name" {
  description = "Cloud KMS Key Ring"
  value       = google_kms_key_ring.imagesense_keyring.name
}

output "gcs_cmek_key_id" {
  description = "CMEK Key for GCS Image Artifacts"
  value       = google_kms_crypto_key.gcs_key.id
}

output "bq_cmek_key_id" {
  description = "CMEK Key for BigQuery Telemetry"
  value       = google_kms_crypto_key.bq_key.id
}

output "vertex_cmek_key_id" {
  description = "CMEK Key for Vertex AI Vector Search"
  value       = google_kms_crypto_key.vertex_key.id
}

output "artifact_bucket_name" {
  description = "CMEK Encrypted GCS Artifact Bucket"
  value       = google_storage_bucket.artifact_bucket.name
}
