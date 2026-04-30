"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { isAuthenticated, removeToken } from "@/lib/auth";

const navItems = [
  { href: "/", label: "대시보드" },
  { href: "/market", label: "시세 조회" },
  { href: "/auto-trade", label: "자동매매" },
  { href: "/portfolio", label: "포트폴리오" },
  { href: "/orders", label: "주문 내역" },
];

export default function Nav() {
  const router = useRouter();

  function handleLogout() {
    removeToken();
    router.push("/login");
  }

  return (
    <header className="border-b border-gray-800 bg-gray-900">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-6 px-4">
        <Link href="/" className="text-lg font-bold text-white">
          KIS Auto Trader
        </Link>
        <nav className="flex flex-1 gap-4">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-sm text-gray-400 hover:text-white transition-colors"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        {isAuthenticated() && (
          <button
            onClick={handleLogout}
            className="text-sm text-gray-500 hover:text-white transition-colors"
          >
            로그아웃
          </button>
        )}
      </div>
    </header>
  );
}
