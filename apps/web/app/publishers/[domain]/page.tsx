import { api } from "@/lib/api";
import Link from "next/link";
import { notFound } from "next/navigation";

type Pub = {
  domain: string; name: string | null; active: boolean;
  top_advertisers: { domain: string; impressions: number }[];
};

export default async function PublisherPage({ params }: { params: Promise<{ domain: string }> }) {
  const { domain } = await params;
  let data: Pub;
  try {
    data = await api<Pub>(`/publishers/${encodeURIComponent(domain)}?days=7`);
  } catch {
    notFound();
  }
  return (
    <main className="p-8 max-w-5xl mx-auto">
      <h1 className="text-2xl font-semibold">{data.name || data.domain}</h1>
      <p className="text-gray-500 mb-6">{data.domain} · {data.active ? "active" : "inactive"}</p>
      <h2 className="text-lg font-medium mb-3">Top Advertisers (7d)</h2>
      <table className="w-full text-sm">
        <thead className="text-left text-gray-500"><tr><th>Domain</th><th>Impressions</th></tr></thead>
        <tbody>
          {data.top_advertisers.map((a) => (
            <tr key={a.domain} className="border-t">
              <td className="py-1"><Link className="underline" href={`/advertisers/${a.domain}`}>{a.domain}</Link></td>
              <td>{a.impressions}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
