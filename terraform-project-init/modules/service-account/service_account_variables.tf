variable "service_accounts" {
  description = "A list of service accounts and roles"
  type = list(object({
    sa_name = string
    sa_role = string
  }))
  default = [
    {
      sa_name = "cloud-run",
      sa_role = "roles/run.admin"
    },
    {
      sa_name = "bigquery",
      sa_role = "roles/bigquery.admin"
    }
  ]
}

variable "project_name" {
  type    = string
  default = "datadice-learning-376715"
}
