export type UserRole = 
  | 'SUPER_ADMIN' 
  | 'SECURITY_ADMIN' 
  | 'DEPARTMENT_ADMIN' 
  | 'AI_ANALYST' 
  | 'GIS_OPERATOR' 
  | 'MAINTENANCE_OFFICER' 
  | 'TECHNICIAN' 
  | 'OPERATOR' 
  | 'POLICE_OFFICER' 
  | 'DEPT_NODAL_OFFICER' 
  | 'AMC_TECHNICIAN';

export interface User {
  id: string;
  name: string;
  email: string;
  username?: string;
  role: UserRole;
  roleTitle: string;
  departmentId?: string;
  departmentName?: string;
  badgeCode: string;
}

export interface Department {
  id: string;
  name: string;
  code: string;
  category: string;
  nodal_officer: string;
  contact_email: string;
  active_cameras: number;
  total_cameras: number;
}

export interface Camera {
  id: string;
  asset_code: string;
  name: string;
  dept_id: string;
  dept_name: string;
  station_division: string;
  responsible_officer: string;
  officer_phone: string;
  state: string;
  district: string;
  taluka: string;
  ward_zone: string;
  latitude: number;
  longitude: number;
  altitude: number;
  fov_azimuth: number;
  fov_angle: number;
  coverage_radius: number;
  camera_type: string;
  resolution: string;
  fps: number;
  bitrate_kbps: number;
  storage_arch: string;
  nvr_ip: string;
  nvr_port: number;
  storage_tb: number;
  retention_days: number;
  link_type: string;
  bandwidth_mbps: number;
  protocol: string;
  stream_url: string;
  ownership: string;
  vendor_name: string;
  amc_expiry: string;
  warranty_status: string;
  status: string;
  is_online: boolean;
  last_ping: string;
  health_score: number;
}

export interface AuditLog {
  id: string;
  camera_id: string;
  timestamp: string;
  user_id: string;
  user_name: string;
  previous_state: string;
  new_state: string;
  justification: string;
}

export interface AnprDetection {
  id: string;
  camera_id: string;
  camera_name: string;
  dept_name: string;
  latitude: number;
  longitude: number;
  plate_number: string;
  vehicle_type: string;
  vehicle_color: string;
  confidence: number;
  timestamp: string;
  snapshot_url: string;
  is_watchlist_hit: boolean;
  watchlist_category?: string;
}

export interface RouteWaypoint {
  step: number;
  detection_id: string;
  camera_id: string;
  camera_name: string;
  dept_name: string;
  latitude: number;
  longitude: number;
  timestamp: string;
  plate_number: string;
  vehicle_type: string;
  vehicle_color: string;
  confidence: number;
  snapshot_url: string;
  is_watchlist_hit: boolean;
  watchlist_category?: string;
  distance_from_prev_km: number;
}

export interface RouteSearchResult {
  query_plate: string;
  total_detections: number;
  total_distance_km: number;
  first_seen: string | null;
  last_seen: string | null;
  waypoints: RouteWaypoint[];
}

export interface WatchlistItem {
  id: string;
  plate_number: string;
  category: string;
  description: string;
  flagged_by: string;
  created_at: string;
  severity: string;
}

export interface MaintenanceTicket {
  id: string;
  ticket_code: string;
  camera_id: string;
  camera_name: string;
  dept_id: string;
  dept_name: string;
  issue_type: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  status: 'Open' | 'Assigned' | 'In Progress' | 'Resolved' | 'Closed';
  created_at: string;
  sla_due_at: string;
  assigned_technician: string;
  vendor_name: string;
  repair_cost_inr: number;
  resolution_summary?: string;
  photo_evidence_url?: string;
}

export interface DashboardStats {
  total_cameras: number;
  online_cameras: number;
  offline_cameras: number;
  system_uptime_percentage: number;
  active_maintenance_tickets: number;
  total_maintenance_tickets: number;
  total_storage_capacity_tb: number;
  total_departments: number;
  department_breakdown: Array<{
    dept_id: string;
    dept_name: string;
    dept_code: string;
    total_cameras: number;
    active_cameras: number;
    uptime_percent: number;
  }>;
  pending_approvals_count?: number;
  alert_trends_7days: Array<{
    date: string;
    anpr_hits: number;
    intrusion_alerts: number;
    offline_incidents: number;
  }>;
}

export interface PendingUser {
  id: string;
  username: string;
  email: string;
  full_name: string;
  employee_id: string;
  department: string;
  created_at: string;
  user_status: string;
}
