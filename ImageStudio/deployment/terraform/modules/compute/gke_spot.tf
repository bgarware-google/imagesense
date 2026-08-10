# ==============================================================================
# GPU Cluster Scaling & Spot / Preemptible Resource Efficiency (GKE / Cloud Run)
# ==============================================================================

# GKE Autopilot / Spot Node Pool for GPU-Accelerated Asynchronous Batch Workers
resource "google_container_cluster" "imagesense_gpu_cluster" {
  name     = "imagesense-batch-cluster-${var.env}"
  location = var.region
  project  = var.project_id

  enable_autopilot = true

  # Strict regional data residency
  ip_allocation_policy {}

  network_policy {
    enabled = true
  }

  release_channel {
    channel = "REGULAR"
  }

  labels = {
    environment = var.env
    workload    = "batch-gpu-rendering"
    managed_by  = "terraform"
  }
}

# Dedicated Spot / Preemptible GPU Node Pool (NVIDIA L4) for 60-80% Cost Reduction
resource "google_container_node_pool" "spot_gpu_pool" {
  name       = "spot-gpu-l4-pool-${var.env}"
  location   = var.region
  cluster    = google_container_cluster.imagesense_gpu_cluster.name
  project    = var.project_id

  node_count = var.env == "prod" ? 2 : 0

  autoscaling {
    min_node_count = 0
    max_node_count = 10
  }

  node_config {
    spot         = true # Preemptible / Spot pricing for 60-80% savings
    machine_type = "g2-standard-4" # NVIDIA L4 GPU instance for rembg / ONNX acceleration

    guest_accelerator {
      type  = "nvidia-l4"
      count = 1
      gpu_driver_installation_config {
        gpu_driver_version = "LATEST"
      }
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      environment = var.env
      tier        = "spot-gpu-worker"
    }

    taint {
      key    = "nvidia.com/gpu"
      value  = "present"
      effect = "NO_SCHEDULE"
    }
  }
}

output "gke_cluster_name" {
  value = google_container_cluster.imagesense_gpu_cluster.name
}
