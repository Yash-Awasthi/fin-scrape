import { NextResponse } from "next/server";
import { getCloudflareContext } from "@opennextjs/cloudflare";

export async function GET() {
  let country = "US";
  let city: string | null = null;
  let lat: string | null = null;
  let lng: string | null = null;

  try {
    const { cf } = getCloudflareContext();
    if (cf) {
      country = (cf.country as string) || "US";
      city = (cf.city as string) || null;
      lat = (cf.latitude as string) || null;
      lng = (cf.longitude as string) || null;
    }
  } catch {
    // Dev mode — no CF context available, defaults apply
  }

  return NextResponse.json({ country, city, lat, lng });
}
