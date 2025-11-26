output "redis_endpoint" {
  description = "Redis primary endpoint"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "redis_port" {
  description = "Redis port"
  value       = aws_elasticache_replication_group.redis.port
}

output "redis_reader_endpoint" {
  description = "Redis reader endpoint (for read replicas)"
  value       = aws_elasticache_replication_group.redis.reader_endpoint_address
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = "rediss://:${var.redis_auth_token}@${aws_elasticache_replication_group.redis.primary_endpoint_address}:${aws_elasticache_replication_group.redis.port}"
  sensitive   = true
}
