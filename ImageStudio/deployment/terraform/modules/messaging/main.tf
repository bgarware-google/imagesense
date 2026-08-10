variable "project_id" { type = string }
variable "env" { type = string }

resource "google_pubsub_topic" "batch_jobs_topic" {
  name    = "imagesense-batch-jobs-${var.env}"
  project = var.project_id
}

resource "google_pubsub_topic" "dead_letter_topic" {
  name    = "imagesense-dlq-${var.env}"
  project = var.project_id
}

resource "google_pubsub_subscription" "batch_subscription" {
  name    = "imagesense-batch-sub-${var.env}"
  topic   = google_pubsub_topic.batch_jobs_topic.name
  project = var.project_id

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter_topic.id
    max_delivery_attempts = 5
  }

  ack_deadline_seconds = 600
}

output "topic_id" {
  value = google_pubsub_topic.batch_jobs_topic.id
}
