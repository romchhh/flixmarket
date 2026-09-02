import { readFileSync } from "node:fs";
import { join } from "node:path";

export type LegalDocId = "oferta" | "policy";

const TITLES: Record<LegalDocId, string> = {
  oferta: "Умови користування та публічна оферта",
  policy: "Політика конфіденційності",
};

export function getLegalTitle(id: LegalDocId): string {
  return TITLES[id];
}

export function getLegalContent(id: LegalDocId): string {
  const filePath = join(process.cwd(), "content", `${id}.txt`);
  return readFileSync(filePath, "utf8").trim();
}
