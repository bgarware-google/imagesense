# ==============================================================================
# BigQuery Telemetry & FinOps Analytics Infrastructure
# ==============================================================================

resource "google_bigquery_table" "finops_telemetry_logs" {
  dataset_id          = google_bigquery_dataset.telemetry_dataset.dataset_id
  table_id            = "finops_telemetry_logs"
  project             = var.project_id
  description         = "Detailed runtime telemetry, token consumption, and FinOps cost tracking table"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  clustering = ["user_id", "feature", "model_name", "status"]

  schema = <<EOF
[
  {
    "name": "timestamp",
    "type": "TIMESTAMP",
    "mode": "REQUIRED",
    "description": "UTC timestamp of request execution"
  },
  {
    "name": "request_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Unique request execution trace ID"
  },
  {
    "name": "user_id",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Authenticated user email or service account identifier"
  },
  {
    "name": "feature",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "ImageStudio pipeline feature invoked"
  },
  {
    "name": "model_name",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Vertex AI foundational model or vision endpoint used"
  },
  {
    "name": "prompt_tokens",
    "type": "INTEGER",
    "mode": "NULLABLE",
    "description": "Estimated prompt input token consumption"
  },
  {
    "name": "completion_tokens",
    "type": "INTEGER",
    "mode": "NULLABLE",
    "description": "Output / completion tokens generated"
  },
  {
    "name": "total_tokens",
    "type": "INTEGER",
    "mode": "NULLABLE",
    "description": "Total combined LLM token consumption"
  },
  {
    "name": "images_count",
    "type": "INTEGER",
    "mode": "NULLABLE",
    "description": "Number of images generated or edited"
  },
  {
    "name": "latency_ms",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "End-to-end execution latency in milliseconds"
  },
  {
    "name": "estimated_cost_usd",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "Calculated real-time cost in USD"
  },
  {
    "name": "action_taken",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Agent routing action: EDIT_EXISTING, GENERATE_SCRATCH, SECURITY_BLOCKED"
  },
  {
    "name": "similarity_score",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "Cosine similarity score against existing vector datastore assets"
  },
  {
    "name": "pii_redacted",
    "type": "BOOLEAN",
    "mode": "NULLABLE",
    "description": "Whether sensitive PII was detected and redacted by Cloud DLP"
  },
  {
    "name": "vision_safe",
    "type": "BOOLEAN",
    "mode": "NULLABLE",
    "description": "Whether image outputs passed Cloud Vision SafeSearch moderation"
  },
  {
    "name": "status",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Execution status: SUCCESS, BLOCKED, ERROR"
  }
]
EOF
}

# -----------------------------------------------------------------------------
# Looker / Looker Studio FinOps Analytical Views
# -----------------------------------------------------------------------------

# View 1: Daily FinOps Cost & Token Consumption Summary
resource "google_bigquery_table" "v_finops_daily_summary" {
  dataset_id = google_bigquery_dataset.telemetry_dataset.dataset_id
  table_id   = "v_finops_daily_summary"
  project    = var.project_id
  description = "Aggregated daily cost, token consumption, and savings for Looker Studio"
  deletion_protection = false

  view {
    query          = <<EOF
SELECT
  DATE(timestamp) AS usage_date,
  user_id,
  feature,
  model_name,
  COUNT(request_id) AS total_requests,
  SUM(total_tokens) AS total_tokens_consumed,
  SUM(images_count) AS total_images_generated,
  AVG(latency_ms) AS avg_latency_ms,
  SUM(estimated_cost_usd) AS total_cost_usd,
  COUNTIF(action_taken = 'EDIT_EXISTING') AS cache_hits_edited,
  COUNTIF(action_taken = 'GENERATE_SCRATCH') AS generated_from_scratch,
  -- Estimated savings from editing existing image ($0.02) vs generating 4 from scratch ($0.12)
  SUM(CASE WHEN action_taken = 'EDIT_EXISTING' THEN 0.10 ELSE 0.0 END) AS estimated_savings_usd,
  COUNTIF(pii_redacted = TRUE) AS pii_redaction_events,
  COUNTIF(status = 'BLOCKED') AS security_blocks
FROM
  `${var.project_id}.${google_bigquery_dataset.telemetry_dataset.dataset_id}.finops_telemetry_logs`
GROUP BY
  1, 2, 3, 4
EOF
    use_legacy_sql = false
  }

  depends_on = [google_bigquery_table.finops_telemetry_logs]
}

# View 2: User / Department Breakdown
resource "google_bigquery_table" "v_finops_user_breakdown" {
  dataset_id = google_bigquery_dataset.telemetry_dataset.dataset_id
  table_id   = "v_finops_user_breakdown"
  project    = var.project_id
  description = "FinOps cost and token attribution per user/service account"
  deletion_protection = false

  view {
    query          = <<EOF
SELECT
  user_id,
  COUNT(request_id) AS total_requests,
  SUM(total_tokens) AS total_tokens,
  SUM(estimated_cost_usd) AS total_spend_usd,
  SUM(CASE WHEN action_taken = 'EDIT_EXISTING' THEN 0.10 ELSE 0.0 END) AS total_saved_usd,
  AVG(latency_ms) AS avg_latency_ms
FROM
  `${var.project_id}.${google_bigquery_dataset.telemetry_dataset.dataset_id}.finops_telemetry_logs`
GROUP BY
  user_id
EOF
    use_legacy_sql = false
  }

  depends_on = [google_bigquery_table.finops_telemetry_logs]
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "bigquery_telemetry_table_id" {
  description = "BigQuery FinOps Telemetry Table ID"
  value       = "${var.project_id}.${google_bigquery_dataset.telemetry_dataset.dataset_id}.${google_bigquery_table.finops_telemetry_logs.table_id}"
}

output "looker_daily_summary_view_id" {
  description = "Looker Studio Daily Summary View ID"
  value       = "${var.project_id}.${google_bigquery_dataset.telemetry_dataset.dataset_id}.${google_bigquery_table.v_finops_daily_summary.table_id}"
}
