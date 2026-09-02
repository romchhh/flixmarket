import Link from "next/link";
import { ChevronLeft } from "lucide-react";

type LegalDocumentProps = {
  title: string;
  content: string;
};

export default function LegalDocument({ title, content }: LegalDocumentProps) {
  const lines = content.split("\n");
  const bodyStart = lines.findIndex((line, i) => i > 0 && line.trim() !== "");
  const body = (bodyStart >= 0 ? lines.slice(bodyStart) : lines).join("\n").trim();

  return (
    <div className="max-w-md mx-auto px-4 pt-4 pb-8">
      <div className="flex items-center gap-2 mb-5">
        <Link
          href="/"
          className="flex items-center justify-center w-9 h-9 rounded-full bg-white border border-gray-100 text-gray-600 hover:bg-gray-50"
          aria-label="Назад"
        >
          <ChevronLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-lg font-bold text-gray-900 leading-snug">{title}</h1>
      </div>

      <article className="rounded-2xl bg-white border border-gray-100 shadow-sm px-4 py-5">
        <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap break-words">
          {body}
        </div>
      </article>
    </div>
  );
}
