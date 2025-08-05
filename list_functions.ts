// ts_lister helper file
import { Project } from "ts-morph";
import path from "path";

const programDir = process.argv[2];
const project = new Project({
  tsConfigFilePath: path.join(programDir, "tsconfig.json"),
});

const sourceFiles = project.getSourceFiles(path.join(programDir, "src/**/*.ts"));

// Collect all externals across all files of a project to be imported in each test
const projectExternals = new Set<string>();
for (const sf of sourceFiles) {
  sf.getImportDeclarations()
    .map(imp => imp.getModuleSpecifierValue())
    .filter(mod => !mod.startsWith("."))
    .forEach(mod => projectExternals.add(mod));
}

// Collect exported functions
const allFns: any[] = [];
for (const sf of sourceFiles) {
  for (const fn of sf.getFunctions()) {
    if (!fn.isExported()) continue;
    const params = fn.getParameters().map(p => ({
      name: p.getName(),
      type: p.getType().getText()
    }));
    allFns.push({
      name: fn.getName(),
      params,
      file: sf.getFilePath(),
    });
  }
}

// Emit both lists together
console.log(JSON.stringify({
  functions: allFns,
  externals: Array.from(projectExternals),
}, null, 2));