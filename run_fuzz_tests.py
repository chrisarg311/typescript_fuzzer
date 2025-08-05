# run_fuzz_tests.py

import subprocess
from pathlib import Path
import yaml

# config management
with open("config.yaml", "r") as yamlConfig:
    config = yaml.safe_load(yamlConfig)

base_dir = Path(__file__).parent.resolve()
fuzz_dir = base_dir / config["fuzz_test_directory"]
fuzz_dir_name = config["fuzz_test_directory"]
display_terminal_messages = config["display_terminal_messages"]
create_comprehensive_log = config["create_comprehensive_log"]
comprehensive_log_name = config["comprehensive_log_name"]

# ts-node execution specification to avoid compilation errors before test execution
ts_node = "npx ts-node --transpile-only --project tsconfig.json"

all_errors = []

def run_project_tests(proj_name: str):
    proj_fuzz = fuzz_dir / proj_name
    log_path = proj_fuzz / f"{proj_name}.log"
    errors = []
    test_files = list(proj_fuzz.glob("*.test.ts"))
    if display_terminal_messages:
        print(f"\nRunning {len(test_files)} tests for project: {proj_name}")
    with log_path.open("w") as logf:
        for i, test_file in enumerate(test_files, 1):
            if display_terminal_messages:
                print(f"  [{i}/{len(test_files)}] Running {test_file.name}...", end=" ")
            cmd = f"{ts_node} --project tsconfig.json {test_file}"
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            logf.write(f"--- {test_file.name} ---\n")
            logf.write(proc.stdout)
            logf.write(proc.stderr)
            if proc.returncode != 0:
                errors.append(f"{proj_name}/{test_file.name}: exit {proc.returncode}")
                if display_terminal_messages:
                    print("Failed")
            else:
                if display_terminal_messages:
                    print("Passed")
            logf.write("\n")
    return errors

def main():
    for proj in fuzz_dir.iterdir():
        if not proj.is_dir(): continue
        errs = run_project_tests(proj.name)
        all_errors.extend(errs)

    # write comprehensive log
    if create_comprehensive_log:
        with (fuzz_dir / comprehensive_log_name).open("w") as f:
            for e in all_errors:
                f.write(e + "\n")
    
    if display_terminal_messages:
        if create_comprehensive_log:
            print(f"\nFinished running all fuzz tests. See {fuzz_dir_name}/*/*.log and {comprehensive_log_name} for details.")
        else:
            print(f"\nFinished running all fuzz tests. See {fuzz_dir_name}/*/*.log for details.")
        

if __name__ == "__main__":
    main()

