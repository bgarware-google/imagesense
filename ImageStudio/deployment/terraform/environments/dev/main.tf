# ==============================================================================
# Development Environment Infrastructure (Strict Regional Residency: us-central1)
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.20"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Security & CMEK Module
module "security" {
  source     = "../../modules/security"
  project_id = var.project_id
  region     = var.region
  env        = "dev"
}

# 2. IAM & Service Accounts Module
module "iam" {
  source     = "../../modules/iam"
  project_id = var.project_id
  env        = "dev"
}

# 3. Storage Module (CMEK Encrypted)
module "storage" {
  source      = "../../modules/storage"
  project_id  = var.project_id
  region      = var.region
  env         = "dev"
  kms_key_id  = module.security.gcs_kms_key_id
}

# 4. Networking & Cloud Armor Ingress Module
module "networking" {
  source      = "../../modules/networking"
  project_id  = var.project_id
  region      = var.region
  env         = "dev"
}

# 5. Compute Module (Cloud Run)
module "compute" {
  source           = "../../modules/compute"
  project_id       = var.project_id
  region           = var.region
  env              = "dev"
  service_account  = module.iam.api_service_account_email
}

# 6. Messaging Module (Pub/Sub)
module "messaging" {
  source     = "../../modules/messaging"
  project_id = var.project_id
  env        = "dev"
}

# 7. Cache & Vector Datastore Module
module "cache" {
  source     = "../../modules/cache"
  project_id = var.project_id
  region     = var.region
  env        = "dev"
}
