/**
 * JobHunt Pro API Contract Types (Unified Schema)
 * Matches FastAPI backend models across web/routers/*.py
 */

export interface SystemCacheStats {
  hits: number;
  misses: number;
  total_requests: number;
  hit_ratio_pct: number;
  active_items: number;
  max_capacity: number;
  l2_redis_active: boolean;
  status: 'HEALTHY' | 'DEGRADED' | 'MAINTENANCE';
}

export interface DeliverabilityShieldMetrics {
  total_sent_365d: number;
  deliverable_rate_pct: number;
  synthetic_blocked_count: number;
  cooldown_enforced_count: number;
  mx_verification_active: boolean;
}

export interface SDROutreachLog {
  id: string;
  campaign_id: string;
  recipient_email: string;
  company_name: string;
  job_title: string;
  status: 'pending' | 'sent' | 'delivered' | 'opened' | 'replied' | 'bounced';
  sent_at: string;
  tracking_id: string;
}

export interface CampaignSummary {
  campaign_id: string;
  name: string;
  total_leads: number;
  emails_sent: number;
  open_rate_pct: number;
  response_rate_pct: number;
  created_at: string;
}

export interface SystemVitalStatsResponse {
  ok: boolean;
  timestamp: string;
  cache_telemetry: SystemCacheStats;
  deliverability_shield: DeliverabilityShieldMetrics;
}
