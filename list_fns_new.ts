#!/usr/bin/env ts-node

import { Project } from "ts-morph";
import path from "path";
import fs from "fs";

// --- Input ---
const repoDir = process.argv[2];
if (!repoDir) {
  console.error("Usage: ts-node list_functions.ts <repo_directory>");
  process.exit(1);
}

// --- Paths ---
const tsconfigPath = path.join(repoDir, "tsconfig.json");
const nodeModulesPath = path.join(repoDir, "node_modules");

// --- Initialize Project ---
let project: Project;

if (fs.existsSync(nodeModulesPath) && fs.existsSync(tsconfigPath)) {
  // Full type resolution mode
   console.error("Using full type resolution (node_modules exists)");
  try {
    project = new Project({ tsConfigFilePath: tsconfigPath });
  } catch (err) {
    console.error("Failed to load tsconfig.json:", err);
    process.exit(1);
  }
} else {
  // Syntax-only mode (no inferred types)
   console.error("Falling back to syntax-only mode (node_modules missing)");
  project = new Project({
    skipAddingFilesFromTsConfig: true,
    compilerOptions: {
      target: 99, // ScriptTarget.Latest
      moduleResolution: 2, // Node
    },
  });
}

// --- Collect source files ---
const sourceFiles = fs.existsSync(tsconfigPath) && project.getSourceFiles().length > 0
  ? project.getSourceFiles("src/**/*.ts")
  : project.addSourceFilesAtPaths(path.join(repoDir, "**/*.ts"));

if (sourceFiles.length === 0) {
  console.error("No TypeScript files found in repo");
}

// --- Extract functions ---
const allFns: any[] = [];

for (const sf of sourceFiles) {
  for (const fn of sf.getFunctions()) {
    if (!fn.isExported()) continue;

    let params;
    if (fs.existsSync(nodeModulesPath)) {
      // Inferred types
      params = fn.getParameters().map(p => ({
        name: p.getName(),
        type: p.getType().getText()
      }));
    } else {
      // Syntax-only types
      params = fn.getParameters().map(p => ({
        name: p.getName(),
        type: p.getTypeNode()?.getText() ?? "any"
      }));
    }

    const fnName = fn.getName() ?? "<anonymous>";
    allFns.push({
      name: fnName,
      params,
      file: sf.getFilePath(),
    });
  }
}

// --- Collect external imports ---
const projectExternals = new Set<string>();
for (const sf of sourceFiles) {
  sf.getImportDeclarations()
    .map(imp => imp.getModuleSpecifierValue())
    .filter(mod => !mod.startsWith("."))
    .forEach(mod => projectExternals.add(mod));
}

// --- Emit JSON ---
console.log(JSON.stringify({
  functions: allFns,
  externals: Array.from(projectExternals),
}, null, 2));

console.error(`Processed ${sourceFiles.length} files`);
console.error(`Found ${allFns.length} exported functions`);
