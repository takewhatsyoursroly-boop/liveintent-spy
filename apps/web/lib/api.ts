const API_URL = process.env.NEXT_PUBLIC_API_URL!;
const ADMIN_TOKEN = process.env.ADMIN_TOKEN!; // server-only

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.headers || {}),
      Authorization: `Bearer ${ADMIN_TOKEN}`,
    },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
  return res.json();
}
