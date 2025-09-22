# create_fuzz_tests.py

import os
import json
import subprocess
import re
from pathlib import Path
import yaml

import tempfile
import signal
import shutil

base_tmp_dir = Path("fuzz_tmp")
base_tmp_dir.mkdir(exist_ok=True)
tmpfolder = tempfile.mkdtemp(dir=base_tmp_dir)

def cleanup(signum, frame):
    shutil.rmtree(base_tmp_dir, ignore_errors=True)
    exit(1)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# config management
with open("config.yaml", "r") as yamlConfig:
    config = yaml.safe_load(yamlConfig)

base_dir = Path(__file__).parent.resolve()
program_dir = base_dir / config["project_directory"]
fuzz_test_dir = base_dir / config["fuzz_test_directory"]
ts_lister = base_dir / config["ts_lister"]
verbosity = config["verbosity"]
display_terminal_messages = config["display_terminal_messages"]


# map TypeScript types to fast-check arbitraries
# TODO: increase specification, fix optional parameters

def make_arb_for(ts_type_input: str) -> str:
    ts_type = ts_type_input.strip()
    # primitives
    if re.fullmatch(r"(number|Number)", ts_type):
        return "fc.float()"
    if re.fullmatch(r"(string|String)", ts_type):
        return "fc.string()"
    if re.fullmatch(r"boolean", ts_type):
        return "fc.boolean()"

    # arrays
    if ts_type.endswith("[]"):
        inner = ts_type[:-2].strip()
        return f"fc.array({make_arb_for(inner)})"

    # fallback
    return "fc.anything()"

# use ts_lister file to grab functions and what they need to import
def run_ts_morph_lister(program_path):
    res = subprocess.run(
        ["npx", "ts-node", ts_lister, str(program_path)],
        capture_output=True, text=True
    )
    data = json.loads(res.stdout)
    return data["functions"], data["externals"]

# help the test file find the function it's importing from the actual source
def make_relative_import(test_file: Path, target_file: str) -> str:
    test_dir = test_file.parent
    target_path = Path(target_file)
    rel_path = os.path.relpath(target_path, test_dir).replace(os.sep, "/")
    if not rel_path.startswith("."):
        rel_path = "./" + rel_path
    if not rel_path.endswith(".ts"):
        rel_path += ".ts"
    return rel_path

# create functionName_fuzz.test.ts for each exported function

def generate_test_file(fn_info, externals, test_file: Path):
    fn_name = fn_info.get("name") or "<anonymous>"
    params  = fn_info.get("params", [])
    file_path = fn_info.get("file", "<unknown>")

    # Mocks referenced libraries
    # TODO: add option to reference only necessary libraries instead of importing everything

    mock_lines = ["import mock from 'mock-require';"]
    for mod in externals:
        mock_lines.append(
            f"try {{ require.resolve('{mod}'); }} catch {{ mock('{mod}', {{}}); }}"
        )

    # Import path 
    import_path = make_relative_import(test_file, file_path)

    # assemble standalone test file
    # if a function takes no parameters, test if it throws an error with no input
    if not params:
        header = "\n".join(mock_lines)
        content = f"""{header}

import {{ {fn_name} }} from '{import_path}';

(() => {{
  try {{
    {fn_name}();
    console.log("{fn_name}() did not throw");
    process.exit(0);
  }} catch (err) {{
    console.error("{fn_name}() threw:", err);
    process.exit(1);
  }}
}})();
"""
        test_file.write_text(content)
        return

    # if a function takes parameters, call the appropriate fast-check syntax
    else:
        arbs      = [make_arb_for(p["type"]) for p in params]
        names     = [p["name"] for p in params]
        arb_list  = ", ".join(arbs)      # e.g. "fc.string(), fc.float()"
        arg_list  = ", ".join(names)      # e.g. "s, n"
        call_expr = f"{fn_name}({arg_list})"

    # assemble standalone test file
    # adjust verbosity inside the fc.assert() block using the yaml config

    content = f"""{chr(10).join(mock_lines)}

import * as fc from 'fast-check';
import {{ {fn_name} }} from '{import_path}';

(() => {{
  try {{
    fc.assert(
      fc.property(
        {arb_list},
        ({arg_list}) => {{ {call_expr}; }}
      ),
      {{ verbose: {verbosity} }},
    );
    console.log("{fn_name} passed");
    process.exit(0);
  }} catch (err) {{
    console.error("{fn_name} failed:", err);
    process.exit(1);
  }}
}})();
"""
    test_file.write_text(content)


def main():
    fuzz_test_dir.mkdir(exist_ok=True)

    # identify which files can be used (requires src/ and tsconfig.json)
    for program_path in program_dir.iterdir():
        if not program_path.is_dir():
            continue
        if not (program_path / "src").exists():
            if display_terminal_messages:
                print(f"[SKIP] No src/ in {program_path.name}")
            continue
        if not (program_path / "tsconfig.json").exists():
            if display_terminal_messages:
                print(f"[SKIP] No tsconfig.json in {program_path.name}")
            continue

        
        project_test_dir = fuzz_test_dir / program_path.name
        if project_test_dir.exists():
            if display_terminal_messages:
                print(f"[SKIP] Fuzz test folder already exists for {program_path.name}")
            continue

        # export all available functions
        if display_terminal_messages:
            print(f"[INFO] Analyzing {program_path.name}")
        functions, externals = run_ts_morph_lister(program_path)
        if not functions:
            continue

        project_test_dir = fuzz_test_dir / program_path.name
        project_test_dir.mkdir(exist_ok=True)

        # create the test file for each function
        for fn_info in functions:
            if "name" in fn_info:
                test_filename = f"{fn_info['name']}_fuzz.test.ts"
            else:
                # fallback behavior, do something better here
                test_filename = "unknown_fuzz.test.ts"
            test_path = project_test_dir / test_filename
            generate_test_file(fn_info, externals, test_path)
        
        if display_terminal_messages:
            print(f"[DONE] {program_path.name} - {len(functions)} functions analyzed.")

if __name__ == "__main__":
    main()
