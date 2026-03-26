terraform {
    required_version = ">= 1.5.0"

    required_providers {
        google = {
            source = "hashicorp/google"
            version = "~> 5.0"
        }
    }

    backend "gcs" {
        bucket = "infra-sentinel-tfstate-project-8ce22ac1-e16d-43af-be2"
        prefix = "staging/terraform.tfstate"
    }
}

provider "google" {
    project = var.project_id
    region = var.region
}

module "networking" {
    source = "../../modules/networking"
    project_id = var.project_id
    region = var.region
}

module "gke" {
    source = "../../modules/gke"
    project_id = var.project_id
    region = var.region

    cluster_name = "infra-sentinel-staging"
    network_id = module.networking.network_id
    subnet_id = module.networking.subnet_id
    pods_range_name = module.networking.pods_range_name
    services_range_name = module.networking.services_range_name  
}