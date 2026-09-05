import { config } from "../config";

// UN Comtrade — global trade flows by commodity (HS codes)

interface ComtradeResult {
  refYear: number;
  reporterDesc: string;
  partnerDesc: string;
  cmdDesc: string;
  primaryValue: number;
  netWgt: number;
}

export async function searchComtrade(
  commodity: string
): Promise<{ country: string; tradeValue: number; description: string }[]> {
  try {
    const { baseUrl, key } = config.datasources.comtrade;
    const params = new URLSearchParams({
      cmdCode: "",
      flowCode: "M", // imports
      reporterCode: "",
      period: "2023",
      motCode: "0",
      partnerCode: "",
    });

    if (key) params.set("subscription-key", key);

    // Search by commodity text
    const searchUrl = `${baseUrl}/get/C/A/HS?${params.toString()}&cmdDesc=${encodeURIComponent(commodity)}`;

    const res = await fetch(searchUrl, {
      headers: { "Content-Type": "application/json" },
      signal: AbortSignal.timeout(10000),
    });

    if (!res.ok) return [];

    const data = await res.json();
    const results: ComtradeResult[] = data.data ?? [];

    return results.slice(0, 20).map((r) => ({
      country: r.reporterDesc,
      tradeValue: r.primaryValue,
      description: r.cmdDesc,
    }));
  } catch (err) {
    console.error("[Comtrade] Search failed:", err);
    return [];
  }
}
