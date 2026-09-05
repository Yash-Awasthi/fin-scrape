// Curated live-news YouTube channels for the LiveTV panel (iframe embeds).
// Channel IDs extracted live from youtube.com/@handle (externalId) — verified
// 2026-09-06. Grouped by country; the panel's filter narrows by any of them.

export interface Channel {
  name: string;
  country: string;
  channelId: string;
}

export const CHANNELS: Channel[] = [
  // USA
  { name: "Fox News", country: "USA", channelId: "UCXIJgqnII2ZOINSWNOGFThA" },
  { name: "CNBC Television", country: "USA", channelId: "UCrp_UI8XtuYfpiqluWLD7Lw" },
  { name: "Bloomberg TV", country: "USA", channelId: "UCdK2BueKxC9VxXh7e1Ne4oQ" },
  { name: "NBC News", country: "USA", channelId: "UCeY0bbntWzzVIaj2z3QigXg" },
  { name: "ABC News Live", country: "USA", channelId: "UCBi2mrWuNuyYy4gbM6fU18Q" },
  { name: "CNN", country: "USA", channelId: "UCupvZG-5ko_eiXAupbDfxWw" },
  // UK
  { name: "BBC News", country: "UK", channelId: "UC16niRr50-MSBwiO3YDb3RA" },
  { name: "Sky News", country: "UK", channelId: "UCoMdktPbSTixAyNGwb-UYkQ" },
  // India
  { name: "NDTV", country: "India", channelId: "UCZFMm1mMw0F81Z37aaEzTUA" },
  { name: "India Today", country: "India", channelId: "UCYPvAwZP8pZhSMW8qs7cVCw" },
  { name: "Times Now", country: "India", channelId: "UCsxOIz6vrUnPI4JNUqm1Scg" },
  { name: "CNBC-TV18", country: "India", channelId: "UCmRbHAgG2k2vDUvb3xsEunQ" },
  { name: "WION", country: "India", channelId: "UC_gUM8rL-Lrg6O3adPW9K1g" },
  { name: "ABP News", country: "India", channelId: "UCRWFSbif-RFENbBrSiez1DA" },
  // China / HK / Taiwan
  { name: "CGTN", country: "China", channelId: "UC61wvHbR3pkaOzE4-P-9r1g" },
  { name: "SCMP", country: "Hong Kong", channelId: "UCyWH3nbNsDlaxx3C0PPInwg" },
  { name: "TaiwanPlus", country: "Taiwan", channelId: "UCCJBSLNtozkO-NqjpPZujiQ" },
  // Japan / Korea
  { name: "NHK World Japan", country: "Japan", channelId: "UCSPEjw8F2nQDtmUKPFNF7_A" },
  { name: "ANN News", country: "Japan", channelId: "UCGCZAYq5Xxojl_tSXcVJhiQ" },
  { name: "YTN", country: "Korea", channelId: "UCvIEHHuZIbXt3I3EWJqnYYg" },
  // Russia / Middle East
  { name: "RT", country: "Russia", channelId: "UCPyFaUSmf_KPlzb4n85rXDg" },
  { name: "Al Jazeera English", country: "Qatar", channelId: "UCNye-wNBqNL5ZzHSJj3l8Bg" },
  { name: "TRT World", country: "Turkey", channelId: "UC7fWeaHhqgM4Ry-RMpM2YYw" },
  // Europe
  { name: "DW News", country: "Germany", channelId: "UCknLrEdhRCp1aegoMqRaCZg" },
  { name: "France 24 English", country: "France", channelId: "UCQfwfsi5VrQ8yKZ-UWmAEFg" },
  { name: "euronews", country: "France", channelId: "UCSrZ3UV4jOidv8ppoVuvW9Q" },
];

export function embedUrl(channelId: string): string {
  return `https://www.youtube.com/embed/live_stream?channel=${channelId}`;
}

export function countries(): string[] {
  return [...new Set(CHANNELS.map((c) => c.country))].sort();
}
