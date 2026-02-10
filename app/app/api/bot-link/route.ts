import { NextResponse } from "next/server";
import path from "path";
import fs from "fs";

function loadEnvFile(envPath: string): Record<string, string> {
  const out: Record<string, string> = {};
  try {
    if (fs.existsSync(envPath)) {
      const content = fs.readFileSync(envPath, "utf8");
      content.split(/\r?\n/).forEach((line) => {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith("#")) {
          const m = trimmed.match(/^([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$/);
          if (m) out[m[1]] = m[2].replace(/^["']|["']$/g, "").trim();
        }
      });
    }
  } catch {
    // ignore
  }
  return out;
}

function loadBotUsernameFromEnv(): string {
  const fromProcess = process.env.BOT_USERNAME?.trim();
  if (fromProcess) return fromProcess.replace(/^@/, "");

  const candidates = [
    path.resolve(process.cwd(), "..", ".env"),
    path.resolve(process.cwd(), ".env"),
    path.resolve(__dirname, "..", "..", "..", "..", "..", ".env"),
    path.resolve(__dirname, "..", "..", "..", "..", ".env"),
  ];
  for (const envPath of candidates) {
    const env = loadEnvFile(envPath);
    const username = env.BOT_USERNAME?.trim();
    if (username) return username.replace(/^@/, "");
  }
  return "";
}

export async function GET() {
  let link =
    process.env.NEXT_PUBLIC_BOT_LINK?.trim() ||
    process.env.BOT_LINK_FOR_REDIRECT?.trim() ||
    "";
  if (!link) {
    const username = loadBotUsernameFromEnv();
    if (username) link = `https://t.me/${username}`;
  }
  return NextResponse.json({ botLink: link });
}
