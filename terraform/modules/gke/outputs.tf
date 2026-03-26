output "cluster_names" {
    value = google_container_cluster.primary.name
}

output "cluster_endpoint" {
    value = google_container_cluster.primary.endpoint
    sensitive = true
}