import { AdminToastProvider } from "@/components/contexts/AdminToastContext";
import AdminGuard from "@/components/admin/AdminGuard";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AdminToastProvider>
      <AdminGuard>{children}</AdminGuard>
    </AdminToastProvider>
  );
}
