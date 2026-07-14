# ==============================================================================
# Cloudflare DNS Failover Configuration (IMP-128)
# Target: JobHunt Pro API Active-Passive Failover
# Provider: Cloudflare (v4.x)
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

# ─── Variables ───────────────────────────────────────────────────────────────

variable "cloudflare_api_token" {
  description = "Cloudflare API Token with Zone.Load Balancers and Account.Load Balancers permissions"
  type        = string
  sensitive   = true
}

variable "cloudflare_zone_id" {
  description = "Cloudflare Zone ID for the target domain"
  type        = string
}

variable "cloudflare_account_id" {
  description = "Cloudflare Account ID"
  type        = string
}

variable "domain" {
  description = "Base domain name (e.g. jobhuntpro.link or jobhunt.pro)"
  type        = string
}

variable "subdomain" {
  description = "Subdomain to route traffic through the load balancer (e.g. api)"
  type        = string
  default     = "api"
}

variable "primary_origin_address" {
  description = "FQDN or IP address of the primary backend origin (e.g. your-app.koyeb.app)"
  type        = string
}

variable "backup_origin_address" {
  description = "FQDN or IP address of the backup backend origin (e.g. jobhunt-pro.fly.dev)"
  type        = string
}

variable "health_check_path" {
  description = "HTTP path for backend health probes"
  type        = string
  default     = "/healthz"
}

variable "health_check_interval" {
  description = "Seconds between active health checks"
  type        = number
  default     = 60
}

variable "health_check_timeout" {
  description = "Seconds to wait before a health check probe is considered failed"
  type        = number
  default     = 5
}

variable "health_check_retries" {
  description = "Consecutive failed checks to mark origin as down, or successful checks to mark it as up"
  type        = number
  default     = 2
}

variable "alert_notification_email" {
  description = "Email address to receive failover alerts"
  type        = string
  default     = "ops@jobhuntpro.link"
}

# ─── Provider Setup ──────────────────────────────────────────────────────────

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# ─── Load Balancer Monitor ───────────────────────────────────────────────────

resource "cloudflare_load_balancer_monitor" "api_health_monitor" {
  account_id     = var.cloudflare_account_id
  type           = "https"
  method         = "GET"
  path           = var.health_check_path
  port           = 443
  
  # Forward Host header matching the target domain for host-based routing
  header {
    header = "Host"
    values = ["${var.subdomain}.${var.domain}"]
  }

  allow_insecure = false
  timeout        = var.health_check_timeout
  retries        = var.health_check_retries
  interval       = var.health_check_interval
  
  # API returns {"status": "ok"} on lightweight endpoint
  expected_body  = "\"status\":\\s*\"ok\""
  expected_codes = "2xx"
  
  description    = "Active HTTPS health check for JobHunt Pro API failover"
}

# ─── Load Balancer Pools ─────────────────────────────────────────────────────

resource "cloudflare_load_balancer_pool" "primary_pool" {
  account_id = var.cloudflare_account_id
  name       = "jobhunt-pro-primary-pool"
  
  origins {
    name    = "primary-backend"
    address = var.primary_origin_address
    enabled = true
    
    # Koyeb / custom targets need the Host header matching their specific address
    header {
      header = "Host"
      values = [var.primary_origin_address]
    }
  }

  monitor            = cloudflare_load_balancer_monitor.api_health_monitor.id
  minimum_origins    = 1
  notification_email = var.alert_notification_email
  description        = "Primary API pool targeting primary cloud backend (Koyeb)"
}

resource "cloudflare_load_balancer_pool" "backup_pool" {
  account_id = var.cloudflare_account_id
  name       = "jobhunt-pro-backup-pool"
  
  origins {
    name    = "backup-backend"
    address = var.backup_origin_address
    enabled = true
    
    # Backup backend host header override
    header {
      header = "Host"
      values = [var.backup_origin_address]
    }
  }

  monitor            = cloudflare_load_balancer_monitor.api_health_monitor.id
  minimum_origins    = 1
  notification_email = var.alert_notification_email
  description        = "Backup API pool targeting fallback cloud backend (Fly.dev / Render / EKS)"
}

# ─── Load Balancer ───────────────────────────────────────────────────────────

resource "cloudflare_load_balancer" "api_lb" {
  zone_id          = var.cloudflare_zone_id
  name             = "${var.subdomain}.${var.domain}" # DNS hostname (e.g. api.jobhunt.pro)
  fallback_pool_id = cloudflare_load_balancer_pool.backup_pool.id
  
  # Active-Passive configuration: order defines priority (primary pool is tried first)
  default_pool_ids = [
    cloudflare_load_balancer_pool.primary_pool.id,
    cloudflare_load_balancer_pool.backup_pool.id
  ]
  
  steering_policy = "off" # Force strict order-of-pools routing for active-passive failover
  proxied         = true  # Enabled Cloudflare Edge Proxy to avoid client-side DNS caching issues
  
  description     = "Active-Passive Cloudflare DNS Failover Load Balancer for JobHunt Pro API"
}

# ─── Outputs ─────────────────────────────────────────────────────────────────

output "load_balancer_hostname" {
  description = "The DNS hostname for the API load balancer"
  value       = cloudflare_load_balancer.api_lb.name
}

output "primary_pool_id" {
  description = "The ID of the primary backend pool"
  value       = cloudflare_load_balancer_pool.primary_pool.id
}

output "backup_pool_id" {
  description = "The ID of the backup backend pool"
  value       = cloudflare_load_balancer_pool.backup_pool.id
}
