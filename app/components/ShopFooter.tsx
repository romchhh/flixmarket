import Link from "next/link";

export default function ShopFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="mt-8 border-t border-gray-100 bg-white/70">
      <div className="max-w-md mx-auto px-4 py-6 text-center">
        <nav className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-sm">
          <Link
            href="/oferta"
            className="text-gray-600 hover:text-violet-600 transition-colors"
          >
            Публічна оферта
          </Link>
          <span className="text-gray-300" aria-hidden>
            ·
          </span>
          <Link
            href="/policy"
            className="text-gray-600 hover:text-violet-600 transition-colors"
          >
            Політика конфіденційності
          </Link>
        </nav>
        <p className="mt-3 text-xs text-gray-400">© {year} FlixMarket</p>
      </div>
    </footer>
  );
}
