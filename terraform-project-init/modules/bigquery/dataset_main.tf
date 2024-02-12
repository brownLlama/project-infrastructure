# Creates all datasets declared in variable.tf file
resource "google_bigquery_dataset" "creating_dataset" {
  count                      = length(var.dataset_name)
  dataset_id                 = var.dataset_name[count.index]
  location                   = var.dataset_location
  delete_contents_on_destroy = true

  labels = {
    owner = var.owners,
  }

  description = "Dataset for ${var.dataset_name[count.index]}"
}

# Imports gsheet
resource "google_bigquery_table" "gsheet_import" {
  count = length(var.google_sheets)

  dataset_id          = var.dataset_name[0]
  table_id            = var.google_sheets[count.index].table_name
  deletion_protection = false

  external_data_configuration {
    autodetect            = true
    source_format         = "GOOGLE_SHEETS"
    ignore_unknown_values = false

    google_sheets_options {
      skip_leading_rows = 1
    }

    source_uris = [
      var.google_sheets[count.index].url,
    ]

    schema = file(var.google_sheets[count.index].schema_path)
  }

  labels = {
    owner = var.owners,
  }

  # Explicitly specifying the dependency on the dataset creation
  depends_on = [google_bigquery_dataset.creating_dataset]
}
