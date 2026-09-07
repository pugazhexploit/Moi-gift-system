export type UserRole = "admin" | "collector" | "viewer";
export type UserStatus = "active" | "suspended" | "inactive";

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  last_login_at?: string | null;
  created_at: string;
  updated_at: string;
}

export type EventStatus = "draft" | "active" | "completed" | "archived";
export type EventType =
  | "wedding"
  | "reception"
  | "birthday"
  | "festival"
  | "temple_event"
  | "family_function"
  | "community_event"
  | "other";

export interface Event {
  event_id: string;
  event_name: string;
  event_type: EventType;
  description: string;
  venue: string;
  event_date: string;
  start_time: string;
  end_time: string;
  status: EventStatus;
  created_by: string;
  assigned_viewers: string[];
  created_at: string;
  updated_at: string;
}

export interface GuestAddress {
  line_1: string;
  line_2?: string;
  city: string;
  district?: string;
  state: string;
  postal_code: string;
  country: string;
}

export interface Guest {
  guest_id: string;
  event_id: string;
  full_name: string;
  phone: string;
  email?: string;
  address: GuestAddress;
  relationship: string;
  family_name: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface Collector {
  collector_id: string;
  user_id: string;
  name: string;
  phone: string;
  employee_code: string;
  status: "active" | "inactive";
  created_at: string;
  updated_at: string;
}

export type PaymentMethod = "cash" | "upi" | "bank_transfer" | "cheque" | "other";
export type TransactionStatus = "pending" | "verified" | "rejected" | "cancelled" | "locked";

export interface Transaction {
  transaction_id: string;
  event_id: string;
  guest_id: string;
  collector_id: string;
  amount: string;
  currency: string;
  payment_method: PaymentMethod;
  transaction_type: string;
  status: TransactionStatus;
  reference_number?: string | null;
  notes?: string;
  created_at: string;
  updated_at: string;
  verified_by?: string | null;
  verified_at?: string | null;
  locked_at?: string | null;
}

export interface Receipt {
  receipt_id: string;
  transaction_id: string;
  event_id: string;
  guest_id: string;
  collector_id: string;
  issued_at: string;
  verification_status: string;
}

export type GiftType = "household_item" | "decorative" | "clothing" | "electronics" | "accessories" | "other";

export interface Gift {
  gift_id: string;
  event_id: string;
  guest_id: string;
  collector_id: string;
  gift_type: GiftType;
  description: string;
  quantity: number;
  estimated_value?: string | null;
  currency: string;
  notes?: string;
  status: string;
  created_at: string;
}

export type ReconciliationStatus = "pending" | "submitted" | "verified" | "mismatch" | "resolved";

export interface Reconciliation {
  reconciliation_id: string;
  event_id: string;
  collector_id: string;
  expected_cash: string;
  actual_cash: string;
  difference: string;
  reason?: string;
  status: ReconciliationStatus;
  submitted_by: string;
  submitted_at: string;
  verified_by?: string | null;
  verified_at?: string | null;
}

export interface DashboardData {
  total_guests: number;
  total_contributions: string;
  total_cash: string;
  total_online: string;
  total_gift_items: number;
  verified_amount: string;
  pending_amount: string;
  number_of_collectors: number;
  unreconciled_amount: string;
  contributions_over_time: Array<{ bucket: string; amount: string; count: number }>;
  payment_method_breakdown: Record<string, string>;
  collector_breakdown: Array<{ collector_id: string; total_amount: string; cash_amount: string; online_amount: string; count: number }>;
  status_breakdown: Record<string, number>;
  gift_category_breakdown: Record<string, number>;
  hourly_collection: Array<{ hour: string; amount: string; count: number }>;
}

export interface AuditLog {
  id: string;
  user_id?: string | null;
  event_id?: string | null;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  old_value: Record<string, any>;
  new_value: Record<string, any>;
  ip_address: string;
  user_agent: string;
  request_id: string;
  timestamp: string;
}

export interface PaginatedData<T> {
  items: T[];
  page: number;
  limit: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: {
    code: string;
    message: string;
  };
}
