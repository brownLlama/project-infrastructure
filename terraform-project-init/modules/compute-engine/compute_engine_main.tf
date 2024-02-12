# Creating SA & Roles for Compute Engine specificly
resource "google_service_account" "instance_service_accounts" {
  for_each     = var.instances
  account_id   = each.value.service_account
  display_name = "${each.value.service_account} deployment"
}

resource "google_project_iam_member" "service_account_iam" {
  for_each = var.instances
  project  = var.project_id
  role     = each.value.service_account_role
  member   = "serviceAccount:${each.value.service_account}@${var.project_id}.iam.gserviceaccount.com"
}

# Create a new instance in Compute Engine
resource "google_compute_instance" "creating_vm_instance" {
  for_each = var.instances

  name         = each.value.name
  machine_type = each.value.machine_type
  zone         = var.zone
  description  = "VM Instance for ${each.value.name}"

  boot_disk {
    initialize_params {
      image = each.value.boot_disk_image
      size  = each.value.boot_disk_size
    }
  }

  network_interface {
    network = "default"
    access_config {
      // Ephemeral external IP will be assigned
    }
  }

  service_account {
    email  = google_service_account.instance_service_accounts[each.key].email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  metadata = {
    startup-script = file(each.value.startup_script_path)
  }

  tags = each.value.tags
}

# Creating HTTP, HTTPS & IAP-SSH Firewall Rules
resource "google_compute_firewall" "http-server" {
  name    = "allow-http"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }

  source_ranges = ["0.0.0.0/0"]
}

resource "google_compute_firewall" "https-server" {
  name    = "allow-https"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }

  source_ranges = ["0.0.0.0/0"]
}

resource "google_compute_firewall" "iap_ssh" {
  name    = "allow-iap-ssh"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["iap-ssh"]
}
