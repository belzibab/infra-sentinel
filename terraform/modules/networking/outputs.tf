output "network_id" {
    value = google_compute_network.vpc
}

output "subnet_id" {
    value = google_compute_subnetwork.subnet
}

output "pods_range_name" {
    value= "pods"  
}

output "services_range_name" {
    value = "services"
}