/**
 * Minimal SSE-over-POST client.
 *
 * `EventSource` only supports GET, but the build recommender takes a JSON body,
 * so we stream the response manually with `fetch` + `ReadableStream` and parse
 * the `text/event-stream` framing ourselves.
 *
 * Frame format (per https://html.spec.whatwg.org/multipage/server-sent-events.html):
 *   event: <name>\n
 *   data: <json>\n
 *   \n
 *
 * We buffer until we see a blank line (`\n\n`) and then parse one event at a time.
 */

export type SSEEvent = { event: string; data: unknown };
export type SSEHandler = (e: SSEEvent) => void;

function parseFrame(raw: string): SSEEvent | null {
  let event = 'message';
  const dataLines: string[] = [];
  for (const line of raw.split('\n')) {
    if (!line || line.startsWith(':')) continue; // comment / blank
    const idx = line.indexOf(':');
    const field = idx === -1 ? line : line.slice(0, idx);
    // SSE spec: a single space after the colon is stripped.
    let value = idx === -1 ? '' : line.slice(idx + 1);
    if (value.startsWith(' ')) value = value.slice(1);
    if (field === 'event') event = value;
    else if (field === 'data') dataLines.push(value);
  }
  if (dataLines.length === 0) return null;
  const dataStr = dataLines.join('\n');
  let data: unknown = dataStr;
  try {
    data = JSON.parse(dataStr);
  } catch {
    // leave as string if not JSON
  }
  return { event, data };
}

export async function postSSE(
  url: string,
  body: unknown,
  onEvent: SSEHandler,
  signal?: AbortSignal,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify(body),
      signal,
    });
  } catch (err) {
    if ((err as { name?: string }).name === 'AbortError') return;
    throw err;
  }

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`SSE request failed: ${res.status} ${text}`);
  }
  if (!res.body) {
    throw new Error('SSE response missing body');
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buf = '';

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });

      // Frames are separated by a blank line. Accept both \n\n and \r\n\r\n.
      let sepIdx: number;
      while (
        (sepIdx = (() => {
          const a = buf.indexOf('\n\n');
          const b = buf.indexOf('\r\n\r\n');
          if (a === -1) return b;
          if (b === -1) return a;
          return Math.min(a, b);
        })()) !== -1
      ) {
        const sepLen = buf.startsWith('\r\n\r\n', sepIdx) ? 4 : 2;
        const raw = buf.slice(0, sepIdx);
        buf = buf.slice(sepIdx + sepLen);
        const parsed = parseFrame(raw);
        if (parsed) onEvent(parsed);
      }
    }
    // Flush any trailing partial frame.
    if (buf.trim()) {
      const parsed = parseFrame(buf);
      if (parsed) onEvent(parsed);
    }
  } catch (err) {
    if ((err as { name?: string }).name === 'AbortError') return;
    throw err;
  }
}
