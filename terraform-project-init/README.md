# Terraform

This Terraform configuration sets up a Google Compute Engine (GCE) instance and initializes tables for a new project on Google Cloud Platform (GCP).

## Prerequisites:

1. **Service Account:** A service account with appropriate permissions. Download the JSON key for this service account, rename it to `terraform_service_account_key.json` and place it in the root directory. Try to give least privilege.

2. **Terraform Installed:** Ensure [Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli) is installed on your machine.

## Structure

There are different modules for different tasks, like creating dataset in BQ, creating Compute Engine Instances and more. All these modules are encapsulate in `main.tf`. One can cherry pick each module as per requirement.

```
terraform
├── modules
│   ├── bigquery
│   │   ├── dataset_main.tf
│   │   └── dataset_variables.tf
│   └── compute-engine
│       └── compute_engine_main.tf
...
...
├── development_gcp_service_account_key.json
├── main.tf
└── README.md
```

### Modules

Each Module represent a specific task on GCP. For example: `bigquery-dataset` -> creates different datasets, `compute-engine` -> create a VM and so on.

## Configuring the project

Before running terraform, please go through all the `*-variables` files and then change their respective values.

## Basics of Terraform

- **Initialize Terraform:**

```bash
terraform init
```

- **Plan and Review:**

  Preview the changes to be made.

```bash
terraform plan
```

- **Apply Changes:**

  This will apply ALL the changes from the `main.tf`.

```bash
terraform apply
```

- **Applying Specific Modules:**

  If you only want to apply changes from a specific module, you can use Terraform's `-target` argument.

```bash
terraform apply -target=module.<MODULE_NAME>
```

- **Destroy**
  Caution: It will delete everything that is created.

```bash
terraform destroy
```

TODO

- schedule the instance
- make script for airflow
