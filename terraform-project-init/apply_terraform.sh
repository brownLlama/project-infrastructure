#!/usr/bin/env bash

terraform init
# terraform plan -out=myplan
terraform plan
terraform apply --auto-approve

# Only to run cretain module.
# terraform apply -target=module.bigquery-dataset "myplan"
# terraform apply -target=model.gsheet-import "myplan"
# terraform apply -target=model.service-account "myplan"
# terraform apply -target=model.compute-engine "myplan"
