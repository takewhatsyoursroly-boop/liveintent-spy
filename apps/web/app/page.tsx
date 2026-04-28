import { api } from "@/lib/api";
import Link from "next/link";

type Advertiser = { domain: string; vertical: string; impressions: number };

export default async function Home() {
  const data = await api<Advertiser[]>("/advertisers?days=7&limit=100");
  const byVertical: Record<string, Advertiser[]> = {};
  for (const a of data) {
    if (a.vertical === "unclassified") continue;
    (byVertical[a.vertical] ??= []).push(a);
  }

  return (
    <main className="p-8 max-w-5xl mx-auto">
      <h1 className="text-2xl font-semibold mb-6">Top Advertisers — Last 7 Days</h1>
      {Object.keys(byVertical).sort().map((vert) => (
        <section key={vert} className="mb-8">
          <h2 className="text-lg font-medium mb-2 capitalize">{vert}</h2>
          <table className="w-full text-sm">
            <thead className="text-left text-gray-500">
              <tr><th>Domain</th><th>Impressions</th></tr>
            </thead>
            <tbody>
              {byVertical[vert].slice(0, 20).map((a) => (
                <tr key={a.domain} className="border-t">
                  <td className="py-1">
                    <Link className="underline" href={`/advertisers/${a.domain}`}>{a.domain}</Link>
                  </td>
                  <td>{a.impressions}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
      {Object.keys(byVertical).length === 0 && (
        <p className="text-gray-500">No impressions yet. Subscribe a publisher and wait for the next cycle.</p>
      )}
    </main>
  );
}
