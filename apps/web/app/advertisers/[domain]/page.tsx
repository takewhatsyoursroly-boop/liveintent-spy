import { api } from "@/lib/api";
import { notFound } from "next/navigation";

type Creative = {
  id: number;
  headline: string | null;
  screenshot_path: string;
  final_landing_url: string | null;
  last_seen_at: string;
};

type AdvertiserDetail = {
  domain: string;
  vertical: string;
  vertical_source: string;
  first_seen_at: string;
  last_seen_at: string;
  creatives: Creative[];
};

export default async function AdvertiserPage({ params }: { params: Promise<{ domain: string }> }) {
  const { domain } = await params;
  let data: AdvertiserDetail;
  try {
    data = await api<AdvertiserDetail>(`/advertisers/${encodeURIComponent(domain)}`);
  } catch {
    notFound();
  }

  return (
    <main className="p-8 max-w-5xl mx-auto">
      <h1 className="text-2xl font-semibold">{data.domain}</h1>
      <p className="text-gray-500 mb-6">
        Vertical: <span className="capitalize">{data.vertical}</span> ({data.vertical_source})
        {" · "}First seen: {new Date(data.first_seen_at).toLocaleDateString()}
      </p>
      <h2 className="text-lg font-medium mb-3">Creatives ({data.creatives.length})</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data.creatives.map((c) => (
          <div key={c.id} className="border rounded p-3">
            <img
              src={`/api/creatives/${c.id}/screenshot`}
              alt="creative"
              className="max-w-full"
            />
            {c.headline && <p className="text-sm mt-2">{c.headline}</p>}
            {c.final_landing_url && (
              <a href={c.final_landing_url} target="_blank" rel="noopener noreferrer"
                 className="text-xs text-blue-600 underline mt-1 block break-all">
                {c.final_landing_url}
              </a>
            )}
            <p className="text-xs text-gray-400 mt-1">
              Last seen {new Date(c.last_seen_at).toLocaleString()}
            </p>
          </div>
        ))}
      </div>
    </main>
  );
}
