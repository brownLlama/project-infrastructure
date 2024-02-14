module "bigquery-dataset" {
  source = "./modules/bigquery"
}

module "compute-engine" {
  source = "./modules/compute-engine"
}

module "service-account" {
  source = "./modules/service-account"
}
