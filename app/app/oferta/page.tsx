import type { Metadata } from "next";
import LegalDocument from "@/components/LegalDocument";
import { getLegalContent, getLegalTitle } from "@/lib/legal";

export const metadata: Metadata = {
  title: "Публічна оферта | Flix Market",
  description: "Умови користування та публічна оферта FlixMarket",
};

export default function OfertaPage() {
  return (
    <LegalDocument
      title={getLegalTitle("oferta")}
      content={getLegalContent("oferta")}
    />
  );
}
