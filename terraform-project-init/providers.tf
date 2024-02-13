terraform {
  required_version = ">= 0.12"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.11"
    }
  }
}

provider "google" {
  credentials = file("./terraform_service_account_key.json")
  project     = var.project_name
  region      = var.project_region
  scopes = [
    "https://www.googleapis.com/auth/drive",         # Google Drive
    "https://www.googleapis.com/auth/bigquery",      # BigQuery
    "https://www.googleapis.com/auth/cloud-platform" # Google Cloud Platform (Compute Engine)
  ]
}
