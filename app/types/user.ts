/** Користувач — прив’язка до Telegram (user_id з init data) */
export interface User {
  id: number;
  user_id: number;   // Telegram user id
  user_name: string | null;
  ref_id: number | null;
  join_date: string | null;
  discounts: number;
}


export interface Subscription {
  id: number;
  user_id: number;
  product_id: number;
  product_name?: string | null;
  product_photo?: string | null;
  start_date: string;
  end_date: string;
  active: number;
  status: string;
}

export interface UserPayment {
  payment_id: string | null;
  invoice_id: string | null;
  product_id: number;
  amount: number;
  status: string | null;
  created_at: string | null;
  payment_type: string | null;
  product_name: string | null;
  product_photo: string | null;
}

/** Повторювана підписка (автосписання кожні N місяців). */
export interface RecurringSubscription {
  id: number;
  product_name: string | null;
  months: number;
  price: number;
  next_payment_date: string | null;
  status: string | null;
  payment_failures: number;
}

export interface SubscriptionPayment {
  id: number;
  subscription_id: number;
  amount: number;
  payment_date: string | null;
  status: string | null;
  product_name: string | null;
}

export interface ReferralInfo {
  partnerBalance: number;
  referralCount: number;
  referralPercent: number;
  referrals: Array<{ user_id: number; user_name: string | null; join_date: string | null }>;
  earningsHistory: Array<{
    buyer_id: number;
    purchase_amount: number;
    credit_amount: number;
    product_name: string | null;
    payment_type: string | null;
    created_at: string | null;
  }>;
}

export interface UserProfile extends User {
  firstName?: string | null;
  lastName?: string | null;
  subscriptions?: Subscription[];
  recurringSubscriptions?: RecurringSubscription[];
  payments?: UserPayment[];
  subscriptionPayments?: SubscriptionPayment[];
  daysOnService?: number | null;
  referral?: ReferralInfo;
}
