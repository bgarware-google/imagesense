# ==============================================================================
# IAM & Least-Privilege Dedicated Service Accounts + WIF Keyless Federation
# ==============================================================================

# -----------------------------------------------------------------------------
# 1. Ingress API Service Account (sa-imagesense-api)
#    Strictly scoped to Vertex AI invocation and cloud storage reads
# -----------------------------------------------------------------------------
resource "google_service_account" "api_sa" {
  account_id   = "sa-imagesense-api"
  display_name = "ImageSense Ingress API Service Account"
  description  = "Dedicated service account for ImageSense API ingress with least privilege"
}

resource "google_project_iam_member" "api_aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_project_iam_member" "api_storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_project_iam_member" "api_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

# -----------------------------------------------------------------------------
# 2. Asynchronous Batch Worker Service Account (sa-imagesense-worker)
#    Strictly scoped to Pub/Sub pull, BigQuery dataset edits, and Secret Manager
# -----------------------------------------------------------------------------
resource "google_service_account" "worker_sa" {
  account_id   = "sa-imagesense-worker"
  display_name = "ImageSense Async Batch Worker Service Account"
  description  = "Dedicated service account for asynchronous queue and batch processing"
}

resource "google_project_iam_member" "worker_pubsub_sub" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.worker_sa.email}"
}

resource "google_project_iam_member" "worker_bq_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.worker_sa.email}"
}

resource "google_project_iam_member" "worker_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.worker_sa.email}"
}

resource "google_project_iam_member" "worker_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.worker_sa.email}"
}

# -----------------------------------------------------------------------------
# 3. Workload Identity Federation (WIF) for Keyless CI/CD
#    Eliminates long-lived service account JSON keys
# -----------------------------------------------------------------------------
resource "google_iam_workload_identity_pool" "cicd_pool" {
  workload_identity_pool_id = "imagesense-cicd-pool"
  display_name              = "ImageSense CI/CD Workload Identity Pool"
  description               = "Identity pool for keyless GitHub Actions / Cloud Build pipelines"
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.cicd_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-actions-provider"
  display_name                       = "GitHub Actions OIDC Provider"
  description                        = "OIDC identity provider for GitHub Actions repository federation"

  attribute_mapping = {
    "google.subject"             = "assertion.sub"
    "attribute.actor"            = "assertion.actor"
    "attribute.repository"       = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
  }

  attribute_condition = "assertion.repository_owner == 'bgarware-google'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Allow GitHub Actions repo to impersonate API Service Account keylessly
resource "google_service_account_iam_member" "wif_api_sa_impersonation" {
  service_account_id = google_service_account.api_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.cicd_pool.name}/attribute.repository/bgarware-google/imagesense"
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "api_service_account_email" {
  description = "Email of the dedicated API Ingress Service Account"
  value       = google_service_account.api_sa.email
}

output "worker_service_account_email" {
  description = "Email of the dedicated Async Batch Worker Service Account"
  value       = google_service_account.worker_sa.email
}

output "workload_identity_provider" {
  description = "Workload Identity Provider resource name for keyless CI/CD"
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}
