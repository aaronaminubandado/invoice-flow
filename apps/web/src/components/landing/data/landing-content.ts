import {
  FileText,
  Users,
  CreditCard,
  Repeat,
  Globe,
  BarChart3,
  UserPlus,
  PenLine,
  Send,
  Wallet,
  Clock,
  Zap,
  Shield,
  TrendingUp,
} from 'lucide-react'

export const heroContent = {
  eyebrow: 'Invoicing for freelancers & agencies',
  headline: 'Invoicing that gets out of your way',
  subhead:
    'Create polished invoices, track what\u2019s overdue, and see revenue in one place \u2014 without spreadsheets or template wrestling.',
  primaryCta: 'Start free',
  secondaryCta: 'See how it works',
  trustLine: 'Free to start \u00b7 No credit card \u00b7 Setup in 2 minutes',
  stats: [
    { value: '$2.4M+', label: 'invoiced on platform' },
    { value: '12k+', label: 'invoices sent monthly' },
    { value: '98%', label: 'on-time delivery rate' },
  ],
}

export const logoCompanies = [
  'Northline Studio',
  'Parcel & Co.',
  'Meridian Labs',
  'Fieldwork Agency',
  'Summit Digital',
  'Clearpath Consulting',
]

export const features = [
  {
    icon: FileText,
    title: 'Professional invoices',
    description:
      'Build clean, branded invoices in minutes. Line items, taxes, and notes \u2014 all in one editor.',
    large: false,
  },
  {
    icon: Users,
    title: 'Client management',
    description:
      'Keep contact details, billing preferences, and invoice history for every client in one place.',
    large: false,
  },
  {
    icon: CreditCard,
    title: 'Payment tracking',
    description:
      'See what\u2019s paid, pending, and overdue at a glance. No more digging through email threads.',
    large: true,
  },
  {
    icon: Repeat,
    title: 'Recurring invoices',
    description:
      'Set the schedule once. Invoice Flow sends on time and flags anything unpaid.',
    large: false,
  },
  {
    icon: Globe,
    title: 'Multi-currency',
    description:
      'Bill clients in USD, EUR, GBP, or JPY. Exchange rates handled so you don\u2019t have to.',
    large: true,
  },
  {
    icon: BarChart3,
    title: 'Revenue analytics',
    description:
      'Monthly trends, collection rates, and outstanding balances \u2014 updated as payments come in.',
    large: false,
  },
]

export const walkthroughSteps = [
  {
    id: 'create',
    label: 'Create',
    title: 'Build an invoice in under a minute',
    description:
      'Pick a client, add line items from your product catalog or type them in. Taxes and totals calculate automatically.',
    screenshotLabel: 'Invoice editor',
  },
  {
    id: 'send',
    label: 'Send',
    title: 'Deliver a polished invoice instantly',
    description:
      'Send via email with a secure link. Clients view, download, and pay without creating an account.',
    screenshotLabel: 'Invoice delivery',
  },
  {
    id: 'track',
    label: 'Track',
    title: 'Know exactly where every payment stands',
    description:
      'Dashboard shows paid, pending, and overdue invoices. Get notified when a client opens or pays.',
    screenshotLabel: 'Payment dashboard',
  },
]

export const workflowSteps = [
  {
    step: 1,
    title: 'Add a client',
    description: 'Save their name, email, and billing details once.',
    icon: UserPlus,
  },
  {
    step: 2,
    title: 'Build an invoice',
    description: 'Add line items, set due dates, and preview before sending.',
    icon: PenLine,
  },
  {
    step: 3,
    title: 'Send and track',
    description: 'Deliver via email link and monitor open and payment status.',
    icon: Send,
  },
  {
    step: 4,
    title: 'Get paid and reconcile',
    description: 'Mark payments received and watch your revenue dashboard update.',
    icon: Wallet,
  },
]

export const benefits = [
  {
    icon: Clock,
    title: 'Less time on admin',
    description: 'Stop copying rows between spreadsheets. Invoices, clients, and payments live in one workspace.',
  },
  {
    icon: Zap,
    title: 'Faster collections',
    description: 'Professional invoices with clear due dates get paid sooner. Track overdue items before they slip.',
  },
  {
    icon: TrendingUp,
    title: 'Clear cash flow',
    description: 'See monthly revenue, outstanding balances, and collection trends without exporting to Excel.',
  },
  {
    icon: Shield,
    title: 'Reliable records',
    description: 'Every invoice, payment, and client interaction is logged and searchable when you need it.',
  },
]

export const testimonials = [
  {
    quote:
      'I used to spend an hour every week on invoicing. Now I send five invoices in ten minutes and actually know who hasn\u2019t paid.',
    name: 'Sarah Chen',
    role: 'Freelance UX Designer',
    company: 'Independent',
    initials: 'SC',
  },
  {
    quote:
      'Our agency bills 40+ clients monthly. Invoice Flow handles recurring invoices and multi-currency without the chaos we had in spreadsheets.',
    name: 'Marcus Webb',
    role: 'Operations Director',
    company: 'Fieldwork Agency',
    initials: 'MW',
  },
  {
    quote:
      'The revenue dashboard replaced three different tools. I can see what\u2019s outstanding before Monday standup without asking finance.',
    name: 'Elena Rodriguez',
    role: 'Founder',
    company: 'Summit Digital',
    initials: 'ER',
  },
]

export const pricingTiers = [
  {
    name: 'Starter',
    price: 'Free',
    period: 'forever',
    description: 'For freelancers sending a handful of invoices each month.',
    highlighted: false,
    features: [
      'Up to 5 invoices per month',
      '1 user',
      'Client management',
      'Email delivery',
      'USD billing',
    ],
    cta: 'Start free',
  },
  {
    name: 'Pro',
    price: '$19',
    period: '/month',
    description: 'For growing freelancers and small teams with regular billing.',
    highlighted: true,
    features: [
      'Unlimited invoices',
      '3 users',
      'Recurring invoices',
      'Multi-currency',
      'Revenue analytics',
      'Payment reminders',
    ],
    cta: 'Start free trial',
  },
  {
    name: 'Business',
    price: '$49',
    period: '/month',
    description: 'For agencies managing multiple clients and team members.',
    highlighted: false,
    features: [
      'Everything in Pro',
      'Unlimited users',
      'Custom branding',
      'Priority support',
      'Data export',
      'Advanced reporting',
    ],
    cta: 'Start free trial',
  },
]

export const faqItems = [
  {
    question: 'What\u2019s included in the free plan?',
    answer:
      'The Starter plan includes up to 5 invoices per month, client management, and email delivery. It\u2019s enough to try Invoice Flow with real clients before upgrading.',
  },
  {
    question: 'Which currencies do you support?',
    answer:
      'Invoice Flow supports USD, EUR, GBP, and JPY out of the box. Pro and Business plans unlock multi-currency billing so you can invoice each client in their preferred currency.',
  },
  {
    question: 'Can I set up recurring invoices?',
    answer:
      'Yes. On Pro and Business plans, you can schedule invoices to send weekly, monthly, or on a custom cadence. Invoice Flow handles delivery and flags unpaid recurring invoices.',
  },
  {
    question: 'Do my clients need an account to view invoices?',
    answer:
      'No. Clients receive a secure link via email. They can view, download, and pay without signing up for anything.',
  },
  {
    question: 'Can I export my data?',
    answer:
      'Business plan users can export invoices, clients, and payment records at any time. Pro users can export individual invoices as PDF.',
  },
  {
    question: 'Can I cancel anytime?',
    answer:
      'Yes. There are no long-term contracts. Cancel from your account settings and you\u2019ll retain access through the end of your billing period.',
  },
]

export const navLinks = [
  { label: 'Features', href: '#features' },
  { label: 'How it works', href: '#walkthrough' },
  { label: 'Pricing', href: '#pricing' },
  { label: 'FAQ', href: '#faq' },
]

export const footerLinks = {
  product: [
    { label: 'Features', href: '#features' },
    { label: 'Pricing', href: '#pricing' },
    { label: 'FAQ', href: '#faq' },
  ],
  company: [
    { label: 'About', href: '#' },
    { label: 'Blog', href: '#' },
    { label: 'Contact', href: '#' },
  ],
  legal: [
    { label: 'Privacy', href: '#' },
    { label: 'Terms', href: '#' },
  ],
}

export const mockInvoices = [
  { id: 'INV-1042', client: 'Northline Studio', amount: 4200, status: 'paid' as const },
  { id: 'INV-1041', client: 'Parcel & Co.', amount: 1850, status: 'pending' as const },
  { id: 'INV-1040', client: 'Meridian Labs', amount: 6300, status: 'paid' as const },
  { id: 'INV-1039', client: 'Fieldwork Agency', amount: 2400, status: 'overdue' as const },
  { id: 'INV-1038', client: 'Summit Digital', amount: 5100, status: 'paid' as const },
]

export const mockStats = [
  { label: 'Total Revenue', value: '$48,250', change: '+12.4%', positive: true },
  { label: 'Total Paid', value: '$41,800', change: '+8.2%', positive: true },
  { label: 'Outstanding', value: '$4,250', change: '-3.1%', positive: true },
  { label: 'Overdue', value: '$2,200', change: '+1 invoice', positive: false },
]

export const mockChartData = [32, 45, 38, 52, 48, 61, 55, 68, 72, 65, 78, 84]
