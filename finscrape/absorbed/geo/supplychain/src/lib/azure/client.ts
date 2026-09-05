import { config } from "../config";

// ============================================================
// Azure OpenAI client — gpt-5-mini reasoning model
// ============================================================

interface ChatMessage {
  role: "system" | "user" | "assistant" | "developer";
  content: string;
}

interface ChatCompletionResponse {
  choices: { message: { content: string } }[];
}

function getBaseEndpoint(): string {
  const endpoint = config.azure.endpoint;
  const match = endpoint.match(/^(https:\/\/[^/]+\.azure\.com)/);
  return match ? match[1] : endpoint;
}

export async function chatCompletion(
  messages: ChatMessage[],
  options: { maxCompletionTokens?: number; responseFormat?: "json" } = {}
): Promise<string> {
  const { apiKey, deployment, apiVersion } = config.azure;
  const baseEndpoint = getBaseEndpoint();

  if (!baseEndpoint || !apiKey) {
    throw new Error("Azure OpenAI credentials not configured");
  }

  const url = `${baseEndpoint}/openai/deployments/${deployment}/chat/completions?api-version=${apiVersion}`;

  const body: Record<string, unknown> = {
    messages,
    max_completion_tokens: options.maxCompletionTokens ?? 16384,
  };

  if (options.responseFormat === "json") {
    body.response_format = { type: "json_object" };
  }

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "api-key": apiKey,
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Azure OpenAI error ${res.status}: ${errText}`);
  }

  const json = (await res.json()) as ChatCompletionResponse;
  return json.choices[0]?.message?.content ?? "";
}

export async function chatCompletionJson<T>(
  systemPrompt: string,
  userPrompt: string,
  options: { maxCompletionTokens?: number } = {}
): Promise<T> {
  const raw = await chatCompletion(
    [
      { role: "developer", content: systemPrompt },
      { role: "user", content: userPrompt },
    ],
    { ...options, responseFormat: "json" }
  );

  if (!raw) {
    throw new Error("Azure OpenAI returned an empty response");
  }

  try {
    return JSON.parse(raw) as T;
  } catch {
    throw new Error(
      `Azure OpenAI returned invalid JSON: ${raw.slice(0, 200)}`
    );
  }
}
