variable "dataset_location" {
  type    = string
  default = "europe-west3"
}

variable "dataset_name" {
  description = "Names of all the datasets"
  type        = list(string)
  default = [
    "1_raw_gsheet",
    "1_raw_shopify",
    "2_prep",
    "3_dwh",
    "4_dashboard",
    "5_export",
    "6_data_science"
  ]
}

variable "google_sheets" {
  description = "List of Google Sheets to import into BigQuery"
  type = list(object({
    url         = string
    table_name  = string
    schema_path = string
  }))
  default = [
    {
      url         = "https://docs.google.com/spreadsheets/d/1PK6EpBy5VIJBEhUIOF1spuegHZgDZI3CDpaGwbcLU4w/",
      table_name  = "revenue_weekly_gsheet"
      schema_path = "modules/bigquery/schema/revenue_weekly.json"
    },
    {
      url         = "https://docs.google.com/spreadsheets/d/1JVodX3UnHdn42BNOcoce9yRUQ8GuoFh73L_Pm1udpoY/",
      table_name  = "orders_weekly_gsheet"
      schema_path = "modules/bigquery/schema/orders_weekly.json"
    }
  ]
}

variable "owners" {
  description = "Owners of all the datasets"
  type        = string
  default     = "datadice-client-name"
}
