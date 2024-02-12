# Creating SAs
resource "google_service_account" "creating_service_account" {
  for_each     = { for sa in var.service_accounts : sa.sa_name => sa }
  account_id   = each.key
  display_name = each.key
  description  = "Service Account for ${each.key}"
}

resource "google_project_iam_member" "service_account_iam" {
  for_each = { for sa in var.service_accounts : sa.sa_name => sa }
  project  = var.project_name
  role     = each.value.sa_role
  member   = "serviceAccount:${each.value.sa_name}@${var.project_name}.iam.gserviceaccount.com"
}
