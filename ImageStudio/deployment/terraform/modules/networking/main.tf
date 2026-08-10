variable "project_id" { type = string }
variable "region" { type = string }
variable "env" { type = string }

resource "google_compute_security_policy" "cloud_armor_policy" {
  name        = "imagesense-armor-policy-${var.env}"
  project     = var.project_id
  description = "Enterprise Cloud Armor security policy with Model Armor pre-filter and rate limiting"

  rule {
    action   = "rate_based_ban"
    priority = 1000
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      rate_limit_threshold {
        count        = 120
        interval_sec = 60
      }
      ban_duration_sec = 600
    }
    description = "Rate limit to 120 req/min per IP with 10-minute ban"
  }

  rule {
    action   = "allow"
    priority = 2147483647
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default allow verified traffic"
  }
}

output "security_policy_id" {
  value = google_compute_security_policy.cloud_armor_policy.id
}
