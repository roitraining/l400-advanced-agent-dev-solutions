output "bucket_name" {
  description = "Name of the bucket holding FAQ files"
  value       = google_storage_bucket.aurora_bay_faqs.name
}

output "discovery_engine_data_store_full_name" {
  description = "Full Discovery Engine data store resource name"
  value       = google_discovery_engine_data_store.aurora_bay_faqs.name
}

output "discovery_engine_data_store_id" {
  description = "Terraform ID for the Discovery Engine data store"
  value       = google_discovery_engine_data_store.aurora_bay_faqs.id
}
