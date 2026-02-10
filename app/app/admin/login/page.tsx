"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function AdminLoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (res.ok) {
        router.push("/admin");
        router.refresh();
      } else {
        setError(data.message || "Невірний логін або пароль");
      }
    } catch {
      setError("Помилка з’єднання");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 px-4">
      <div className="w-full max-w-md">
        <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-lg">
          <h1 className="mb-2 text-center text-2xl font-bold text-gray-900">
            Вхід в адмін-панель
          </h1>
          <p className="mb-6 text-center text-sm text-gray-500">
            Flix Market
          </p>
          {error && (
            <div className="mb-6 rounded-lg bg-red-50 p-4 text-sm text-red-600">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="username" className="mb-1.5 block text-sm font-medium text-gray-700">
                Логін
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
                className="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-500/20"
                placeholder="Логін"
              />
            </div>
            <div>
              <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-gray-700">
                Пароль
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                className="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-500/20"
                placeholder="Пароль"
              />
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full rounded-lg bg-violet-600 px-4 py-3 font-semibold text-white hover:bg-violet-700 focus:outline-none focus:ring-2 focus:ring-violet-500/50 disabled:opacity-50"
            >
              {isLoading ? "Вхід…" : "Увійти"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
