// Dev-only helper: generate a batch of sample bookmarks for local testing.
// Not imported by the application — runs via `npm run seed`. lodash is a
// devDependency and only used here.
import _ from "lodash";
import { writeFileSync } from "node:fs";

const domains = ["docs", "wiki", "status", "grafana", "ci"];
const rows = _.range(1, 21).map((i) => ({
  title: _.startCase(`team resource ${i}`),
  url: `https://${_.sample(domains)}.example.com/${i}`,
}));

writeFileSync("seed-bookmarks.json", JSON.stringify(rows, null, 2));
console.log(`wrote ${rows.length} sample bookmarks`);
