terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" {
  type        = string
  description = "GCP Project ID"
  default     = "gdc-ai-playground"
}

variable "region" {
  type        = string
  description = "GCP Region for Cloud Run"
  default     = "us-central1"
}

variable "service_name" {
  type        = string
  description = "Cloud Run service name"
  default     = "image-studio"
}

variable "domain_name" {
  type        = string
  description = "Custom domain name for SSL certificate (optional)"
  default     = ""
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# -----------------------------------------------------------------------------
# 1. Cloud Armor Security Policy
# -----------------------------------------------------------------------------
resource "google_compute_security_policy" "image_studio_armor" {
  name        = "${var.service_name}-cloud-armor-policy"
  description = "Cloud Armor Security Policy for Image Studio Ingress Protection"

  # Adaptive Protection for Layer 7 DDoS mitigation
  adaptive_protection_config {
    layer_7_ddos_defense_config {
      enable = true
    }
  }

  # Rate Limiting Rule: 120 requests per minute per IP
  rule {
    action   = "rate_based_ban"
    priority = "1000"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 120
        interval_sec = 60
      }
      ban_duration_sec = 300
    }
    description = "Rate limit traffic to 120 requests per minute per IP"
  }

  # WAF Rule: Cross-Site Scripting (XSS) Protection
  rule {
    action   = "deny(403)"
    priority = "2000"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('xss-v33-stable')"
      }
    }
    description = "Block OWASP Top 10 XSS attacks"
  }

  # WAF Rule: SQL Injection (SQLi) Protection
  rule {
    action   = "deny(403)"
    priority = "2100"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('sqli-v33-stable')"
      }
    }
    description = "Block SQL Injection attempts"
  }

  # WAF Rule: Scanner / Malicious User-Agent Detection
  rule {
    action   = "deny(403)"
    priority = "2200"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('scannerdetection-v33-stable')"
      }
    }
    description = "Block known vulnerability scanners and malicious probes"
  }

  # WAF Rule: Protocol Attack Protection
  rule {
    action   = "deny(403)"
    priority = "2300"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('protocolattack-v33-stable')"
      }
    }
    description = "Block HTTP protocol violation attacks"
  }

  # Default rule: Allow all legitimate traffic
  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default allow rule"
  }
}

# -----------------------------------------------------------------------------
# 2. Serverless Network Endpoint Group (NEG) for Cloud Run
# -----------------------------------------------------------------------------
resource "google_compute_region_network_endpoint_group" "serverless_neg" {
  name                  = "${var.service_name}-serverless-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = var.service_name
  }
}

# -----------------------------------------------------------------------------
# 3. Global Backend Service with Cloud Armor Attachment
# -----------------------------------------------------------------------------
resource "google_compute_backend_service" "image_studio_backend" {
  name                  = "${var.service_name}-backend-service"
  protocol              = "HTTPS"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  security_policy       = google_compute_security_policy.image_studio_armor.id

  backend {
    group = google_compute_region_network_endpoint_group.serverless_neg.id
  }

  # CDN caching disabled for real-time generative AI endpoints
  enable_cdn = false
}

# -----------------------------------------------------------------------------
# 4. URL Map & Routing
# -----------------------------------------------------------------------------
resource "google_compute_url_map" "url_map" {
  name            = "${var.service_name}-url-map"
  default_service = google_compute_backend_service.image_studio_backend.id
}

# -----------------------------------------------------------------------------
# 5. Global Reserved Static IP Address
# -----------------------------------------------------------------------------
resource "google_compute_global_address" "lb_ip" {
  name = "${var.service_name}-lb-ip"
}

# -----------------------------------------------------------------------------
# 6. HTTP Target Proxy & Forwarding Rule
# -----------------------------------------------------------------------------
resource "google_compute_target_http_proxy" "http_proxy" {
  name    = "${var.service_name}-http-proxy"
  url_map = google_compute_url_map.url_map.id
}

resource "google_compute_global_forwarding_rule" "http_forwarding_rule" {
  name                  = "${var.service_name}-http-forwarding-rule"
  target                = google_compute_target_http_proxy.http_proxy.id
  ip_address            = google_compute_global_address.lb_ip.address
  port_range            = "80"
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "load_balancer_ip" {
  description = "Public IP address of the Cloud Armor protected Load Balancer"
  value       = google_compute_global_address.lb_ip.address
}

output "cloud_armor_policy_name" {
  description = "Name of the Cloud Armor security policy"
  value       = google_compute_security_policy.image_studio_armor.name
}
