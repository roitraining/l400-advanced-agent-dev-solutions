variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "location" {
  description = "Discovery Engine location"
  type        = string
  default     = "global"
}

variable "bucket_location" {
  description = "Cloud Storage bucket location"
  type        = string
  default     = "US"
}
