# ==============================================================================
# GPU Cluster Scaling & Spot / Preemptible Resource Efficiency (GKE / Cloud Run)
# ==============================================================================

resource "google_container_cluster" "imagesense_gpu_cluster" {
  name     = "imagesense-batch-cluster"
  location = var.region
  project  = var.project_id

  enable_autopilot = true

  ip_allocation_policy {}

  release_channel {
    channel = "REGULAR"
  }

  labels = {
    workload   = "batch-gpu-rendering"
    managed_by = "terraform"
  }
}

resource "google_container_node_pool" "spot_gpu_pool" {
  name     = "spot-gpu-l4-pool"
  location = var.region
  cluster  = google_container_cluster.imagesense_gpu_cluster.name
  project  = var.project_id

  autoscaling {
    min_node_count = 0
    max_node_count = 10
  }

  node_config {
    spot         = true # Preemptible / Spot pricing for 60-80% cost savings
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
      tier = "spot-gpu-worker"
    }
  }
}

output "gke_gpu_cluster_name" {
  description = "GKE Spot GPU Cluster for Batch Workloads"
  value       = google_container_cluster.imagesense_gpu_cluster.name
}
