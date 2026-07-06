import axios from "axios";

// Outbound URL preview: fetch a remote URL and report status + a snippet.
// Options come from the request query string (?timeout=..&maxRedirects=..).
export function parseFetchOptions(rawQuery) {
  const params = new URLSearchParams(rawQuery);
  const timeout = Number(params.get("timeout")) || 5000;
  const maxRedirects =
    params.get("maxRedirects") === null ? 5 : Number(params.get("maxRedirects"));
  return { timeout, maxRedirects };
}

export async function preview(url, rawQuery = "") {
  const { timeout, maxRedirects } = parseFetchOptions(rawQuery);
  const res = await axios.get(url, {
    timeout,
    maxRedirects,
    validateStatus: () => true,
  });
  const body = typeof res.data === "string" ? res.data : JSON.stringify(res.data);
  return {
    status: res.status,
    contentType: res.headers["content-type"] || null,
    snippet: body.slice(0, 200),
  };
}
