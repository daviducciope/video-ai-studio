import { existsSync } from "node:fs";
import { resolve } from "node:path";

const files = [
  "src/app/page.tsx",
  "src/app/projects/new/page.tsx",
  "src/app/projects/[projectId]/page.tsx",
];

for (const file of files) {
  if (!existsSync(resolve(process.cwd(), file))) {
    throw new Error(`Missing required file: ${file}`);
  }
}

console.log("web smoke ok");
