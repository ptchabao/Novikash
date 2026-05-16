export type StaffRole = "SUPERADMIN" | "ADMIN" | "SUPPORT" | "AUDITOR";

export interface StaffMe {
  id: number;
  phone: string;
  email?: string;
  role: StaffRole;
  permissions: string[];
}

export interface Wallet {
  id: number;
  balance_available: number;
  balance_locked: number;
  currency: string;
}

export interface AdminUser {
  id: number;
  phone: string;
  email?: string;
  role: string;
  is_verified: boolean;
  is_kyc_verified: boolean;
  identity_type?: string;
  identity_number?: string;
  identity_document_url?: string;
  created_at: string;
  wallet?: Wallet;
}

export interface DashboardStats {
  total_users: number;
  verified_users: number;
  pending_kyc: number;
  total_wallet_balance: number;
  total_locked_balance: number;
  active_loans: number;
  pending_loans: number;
  pending_novi_plus: number;
  transactions_today: number;
  deposits_today: number;
  withdrawals_today: number;
  manual_credits_today: number;
}

export interface Transaction {
  id: number;
  amount: number;
  currency: string;
  exchange_rate: number;
  type: string;
  status: string;
  reference: string;
  created_at: string;
  processed_at?: string;
  sender_wallet_id?: number;
  receiver_wallet_id?: number;
  sender_phone?: string;
  receiver_phone?: string;
}

export interface Loan {
  id: number;
  borrower_id: number;
  borrower_phone?: string;
  loan_type: string;
  amount: number;
  interest_rate: number;
  total_amount: number;
  status: string;
  due_date: string;
  created_at: string;
}

export interface NoviPlusProfile {
  id: number;
  user_id: number;
  user_phone?: string;
  first_name: string;
  last_name: string;
  employer: string;
  contract_type: string;
  contract_end_date?: string;
  partner_bank: string;
  account_number: string;
  declared_salary: number;
  verified_salary?: number;
  status: string;
  rejection_reason?: string;
  submitted_at?: string;
  activated_at?: string;
}
