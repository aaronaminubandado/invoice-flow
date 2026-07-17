export function LogoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <rect width="32" height="32" rx="8" className="fill-primary/15" />
      <path
        d="M8 10h16v2H8V10zm0 5h11v2H8v-2zm0 5h14v2H8v-2z"
        className="fill-primary"
      />
      <circle cx="24" cy="22" r="3" className="fill-primary" />
    </svg>
  )
}
