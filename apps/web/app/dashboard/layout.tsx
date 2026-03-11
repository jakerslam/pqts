import { DashboardShell } from "@/components/dashboard-shell";
import { buildTrustStatusSnapshot } from "@/lib/system/trust-status";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const trustSnapshot = buildTrustStatusSnapshot();
  return <DashboardShell trustSnapshot={trustSnapshot}>{children}</DashboardShell>;
}
