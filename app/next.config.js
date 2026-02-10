const path = require("path");
const fs = require("fs");
const envPath = path.resolve(__dirname, "..", ".env");
if (fs.existsSync(envPath)) {
  const content = fs.readFileSync(envPath, "utf8");
  content.split(/\r?\n/).forEach((line) => {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith("#")) {
      const m = trimmed.match(/^([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$/);
      if (m) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "").trim();
    }
  });
  if (process.env.BOT_USERNAME && !process.env.NEXT_PUBLIC_BOT_USERNAME) {
    process.env.NEXT_PUBLIC_BOT_USERNAME = process.env.BOT_USERNAME.replace(/^@/, "");
  }
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};

module.exports = nextConfig;
