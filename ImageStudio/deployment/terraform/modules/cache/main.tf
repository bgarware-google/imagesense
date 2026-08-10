variable "project_id" { type = string }
variable "region" { type = string }
variable "env" { type = string }

resource "google_discovery_engine_data_store" "imagesense_datastore" {
  location                     = "global"
  data_store_id                = "imagesense-vector-cache-${var.env}"
  display_name                 = "ImageSense Vector Datastore (${var.env})"
  industry_vertical            = "GENERIC"
  content_config               = "NO_CONTENT"
  solution_types               = ["SOLUTION_TYPE_SEARCH"]
  project                      = var.project_id
  create_advanced_site_search  = false
}

output "datastore_id" {
  value = google_discovery_engine_data_store.imagesense_datastore.data_store_id
}
