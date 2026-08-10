variable "project_id" {
  type        = string
  description = "GCP Project ID"
  default     = "gdc-ai-playground"
}

variable "region" {
  type        = string
  description = "Strict regional residency pinned region"
  default     = "us-central1"
}
