import { NextRequest, NextResponse } from "next/server";
import { isAdminValid, setAdminSession } from "@/lib/admin-auth";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const username = typeof body.username === "string" ? body.username.trim() : "";
    const password = typeof body.password === "string" ? body.password : "";

    if (!username || !password) {
      return NextResponse.json(
        { message: "Username and password required" },
        { status: 400 }
      );
    }

    if (!isAdminValid(username, password)) {
      return NextResponse.json(
        { message: "Невірний логін або пароль" },
        { status: 401 }
      );
    }

    await setAdminSession();
    return NextResponse.json({ ok: true });
  } catch {
    return NextResponse.json(
      { message: "Помилка сервера" },
      { status: 500 }
    );
  }
}
