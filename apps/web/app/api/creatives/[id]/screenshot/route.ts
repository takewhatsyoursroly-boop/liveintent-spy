import { NextResponse } from "next/server";

export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const r = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/creatives/${id}/screenshot`, {
    headers: { Authorization: `Bearer ${process.env.ADMIN_TOKEN}` },
  });
  if (!r.ok) return new NextResponse(null, { status: 404 });
  return new NextResponse(r.body, {
    headers: { "Content-Type": r.headers.get("Content-Type") || "image/png" },
  });
}
