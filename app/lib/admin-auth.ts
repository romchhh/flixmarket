import { cookies } from "next/headers";

const ADMIN_COOKIE = "flix_admin_session";
const MAX_AGE = 60 * 60 * 24 * 7; // 7 days

export function getAdminCredentials(): { username: string; password: string } {
  const username = process.env.ADMIN_USERNAME ?? "";
  const password = process.env.ADMIN_PASSWORD ?? "";
  return { username, password };
}

export function isAdminValid(username: string, password: string): boolean {
  const { username: u, password: p } = getAdminCredentials();
  return Boolean(u && p && username === u && password === p);
}

export async function setAdminSession(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.set(ADMIN_COOKIE, "1", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: MAX_AGE,
    path: "/",
  });
}

export async function clearAdminSession(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(ADMIN_COOKIE);
}

export async function getAdminSession(): Promise<boolean> {
  const cookieStore = await cookies();
  const v = cookieStore.get(ADMIN_COOKIE)?.value;
  return v === "1";
}
