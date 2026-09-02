import type { Metadata } from "next";
import LegalDocument from "@/components/LegalDocument";
import { getLegalContent, getLegalTitle } from "@/lib/legal";

export const metadata: Metadata = {
  title: "Політика конфіденційності | Flix Market",
  description: "Політика конфіденційності FlixMarket",
};

export default function PolicyPage() {
  return (
    <LegalDocument
      title={getLegalTitle("policy")}
      content={getLegalContent("policy")}
    />
  );
}
