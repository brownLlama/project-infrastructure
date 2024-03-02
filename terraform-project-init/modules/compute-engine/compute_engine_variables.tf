variable "instances" {
  type = map(object({
    name                 = string
    machine_type         = string
    boot_disk_image      = string
    boot_disk_size       = number
    service_account      = string
    service_account_role = string
    startup_script_path  = string
    tags                 = list(string)
  }))
  default = {
    # "airbyte" = {
    #   name                 = "airbyte"
    #   machine_type         = "e2-highmem-2"
    #   boot_disk_image      = "ubuntu-os-cloud/ubuntu-2204-lts"
    #   boot_disk_size       = 100
    #   service_account      = "airbyte"
    #   service_account_role = "roles/compute.admin"
    #   startup_script_path  = "modules/compute-engine/startup_script/airbyte.sh"
    #   tags                 = ["http-server", "https-server", "iap-ssh"]
    # },
    "airflow" = {
      name                 = "airflow"
      machine_type         = "e2-highmem-2"
      boot_disk_image      = "ubuntu-os-cloud/ubuntu-2204-lts"
      boot_disk_size       = 100
      service_account      = "airflow"
      service_account_role = "roles/compute.admin"
      startup_script_path  = "modules/compute-engine/startup_script/airbyte.sh"
      tags                 = ["http-server", "https-server", "iap-ssh"]
    }
  }
}

variable "project_id" {
  type    = string
  default = "datadice-learning-376715"
}

variable "zone" {
  type    = string
  default = "europe-west3-a"
}
