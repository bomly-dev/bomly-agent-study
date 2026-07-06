import request from "request";
import { parseStringPromise } from "xml2js";

// Import bookmarks from a remote XML feed. Legacy code path: it still uses the
// (deprecated) `request` library because it was written years ago and never
// migrated. `request` is the only thing pulling tough-cookie into the graph.
export function fetchXml(url) {
  return new Promise((resolve, reject) => {
    request({ url, method: "GET", jar: true }, (err, res, body) => {
      if (err) return reject(err);
      if (res.statusCode >= 400) {
        return reject(new Error(`upstream ${res.statusCode}`));
      }
      resolve(body);
    });
  });
}

export async function importBookmarks(xmlString) {
  const doc = await parseStringPromise(xmlString, { explicitArray: false });
  const items = doc?.bookmarks?.bookmark;
  if (!items) return [];
  const list = Array.isArray(items) ? items : [items];
  return list.map((b) => ({ title: b.title, url: b.url }));
}
