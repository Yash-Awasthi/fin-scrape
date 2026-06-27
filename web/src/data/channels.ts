// Curated live-news YouTube channels for the LiveTV panel (iframe embeds).
// Reference pattern only — channel live streams via YouTube's live_stream embed.

export interface Channel {
  name: string;
  channelId: string;
}

export const CHANNELS: Channel[] = [
  { name: "Al Jazeera English", channelId: "UCNye-wNBqNL5ZzHSJj3l8Bg" },
  { name: "DW News", channelId: "UCknLrEdhRCp1aegoMqRaCZg" },
  { name: "France 24 English", channelId: "UCQfwfsi5VrQ8yKZ-UWmAEFg" },
  { name: "Sky News", channelId: "UCoMdktPbSTixAyNGwb-UYkQ" },
];

export function embedUrl(channelId: string): string {
  return `https://www.youtube.com/embed/live_stream?channel=${channelId}`;
}
