resource "random_id" "bucket_suffix" {
  byte_length = 3
}

locals {
  faq_dir   = "${path.module}/../rag-data-store/aurora-bay-alaska-faqs"
  faq_files = fileset(local.faq_dir, "*.txt")
  faq_content_hash = sha1(join("", [for f in sort(tolist(local.faq_files)) : filesha256("${local.faq_dir}/${f}")]))
}

resource "google_project_service" "discovery_engine" {
  project            = var.project_id
  service            = "discoveryengine.googleapis.com"
  disable_on_destroy = false

  depends_on = [
    google_project_service.cloud_resource_manager,
    google_project_service.service_usage,
  ]
}

resource "google_project_service" "cloud_resource_manager" {
  project            = var.project_id
  service            = "cloudresourcemanager.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "service_usage" {
  project            = var.project_id
  service            = "serviceusage.googleapis.com"
  disable_on_destroy = false
}

resource "google_storage_bucket" "aurora_bay_faqs" {
  name                        = "aurora-bay-faqs-${random_id.bucket_suffix.hex}"
  location                    = var.bucket_location
  uniform_bucket_level_access = true
  force_destroy               = true
}

resource "google_storage_bucket_object" "faq_files" {
  for_each = local.faq_files

  name         = "aurora-bay-alaska-faqs/${each.value}"
  bucket       = google_storage_bucket.aurora_bay_faqs.name
  source       = "${local.faq_dir}/${each.value}"
  content_type = "text/plain"
}

resource "google_discovery_engine_data_store" "aurora_bay_faqs" {
  provider = google-beta

  depends_on = [google_project_service.discovery_engine]

  location          = var.location
  data_store_id     = "aurora-bay-faqs-${random_id.bucket_suffix.hex}"
  display_name      = "Aurora Bay FAQs ${random_id.bucket_suffix.hex}"
  industry_vertical = "GENERIC"
  content_config    = "CONTENT_REQUIRED"
}

resource "terraform_data" "import_documents" {
  triggers_replace = [
    google_storage_bucket.aurora_bay_faqs.name,
    google_discovery_engine_data_store.aurora_bay_faqs.data_store_id,
    local.faq_content_hash,
  ]

  provisioner "local-exec" {
    command = "${path.module}/scripts/import_discovery_docs.sh ${var.project_id} ${var.location} ${google_discovery_engine_data_store.aurora_bay_faqs.data_store_id} ${google_storage_bucket.aurora_bay_faqs.name}"
  }

  depends_on = [
    google_storage_bucket_object.faq_files,
    google_discovery_engine_data_store.aurora_bay_faqs,
  ]
}
