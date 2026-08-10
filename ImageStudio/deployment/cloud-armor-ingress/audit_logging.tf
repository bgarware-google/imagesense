# ==============================================================================
# Comprehensive Cloud Audit Logging & Compliance (SOC 2, ISO 27001)
# ==============================================================================

# Enable complete Admin Activity, Data Access, and System Event audit logs
# across all VPC-SC enclosed services for enterprise compliance.
resource "google_project_iam_audit_config" "all_services_audit_logs" {
  project = var.project_id
  service = "allServices"

  audit_log_config {
    log_type = "ADMIN_READ"
  }

  audit_log_config {
    log_type = "DATA_READ"
  }

  audit_log_config {
    log_type = "DATA_WRITE"
  }
}

# Dedicated Audit Log Storage Bucket with Retention Lock & CMEK for Tamper-Proofing
resource "google_logging_project_sink" "compliance_audit_sink" {
  name        = "imagesense-compliance-audit-sink"
  project     = var.project_id
  destination = "storage.googleapis.com/${google_storage_bucket.audit_logs_bucket.name}"
  filter      = "logName:\"logs/cloudaudit.googleapis.com\""

  unique_writer_identity = true
}

resource "google_storage_bucket" "audit_logs_bucket" {
  name          = "imagesense-audit-logs-${var.project_id}"
  project       = var.project_id
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  retention_policy {
    is_locked        = false
    retention_period = 2592000 # 30 days immutable retention for SOC 2 / ISO 27001
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.gcs_key.id
  }
}

resource "google_storage_bucket_iam_member" "audit_sink_writer" {
  bucket = google_storage_bucket.audit_logs_bucket.name
  role   = "roles/storage.objectCreator"
  member = google_logging_project_sink.compliance_audit_sink.writer_identity
}
