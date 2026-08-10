variable "project_id" { type = string }
variable "region" { type = string }
variable "env" { type = string }

resource "google_kms_key_ring" "imagesense_keyring" {
  name     = "imagesense-keyring-${var.env}"
  project  = var.project_id
  location = var.region
}

resource "google_kms_crypto_key" "gcs_key" {
  name            = "imagesense-gcs-cmek-${var.env}"
  key_ring        = google_kms_key_ring.imagesense_keyring.id
  rotation_period = "7776000s" # 90 days
}

resource "google_kms_crypto_key" "bq_key" {
  name            = "imagesense-bq-cmek-${var.env}"
  key_ring        = google_kms_key_ring.imagesense_keyring.id
  rotation_period = "7776000s"
}

output "gcs_kms_key_id" {
  value = google_kms_crypto_key.gcs_key.id
}

output "bq_kms_key_id" {
  value = google_kms_crypto_key.bq_key.id
}
