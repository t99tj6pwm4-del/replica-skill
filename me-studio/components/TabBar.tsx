"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  {
    href: "/create",
    label: "Create",
    icon: <path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3zM19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15z" fill="currentColor" />,
  },
  {
    href: "/gallery",
    label: "Gallery",
    icon: (
      <g fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round">
        <rect x="3" y="4" width="18" height="16" rx="3" />
        <path d="M3 16l5-5 4 4 3-3 6 6" />
      </g>
    ),
  },
  {
    href: "/settings",
    label: "Settings",
    icon: (
      <g fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="3" />
        <path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1" strokeLinecap="round" />
      </g>
    ),
  },
];

export default function TabBar() {
  const path = usePathname();
  return (
    <div className="tabbar">
      <nav aria-label="Main">
        {tabs.map((t) => (
          <Link key={t.href} href={t.href} aria-current={path === t.href ? "page" : undefined}>
            <svg viewBox="0 0 24 24" aria-hidden="true">{t.icon}</svg>
            {t.label}
          </Link>
        ))}
      </nav>
    </div>
  );
}
