---Typescript Fuzzer Documentation---

---Purpose:
Fuzz test TypeScript Projects by extracting their functions
and using fast-check to fuzz them

---File structure:
create_fuzz_tests.py, run_fuzz_tests.py, and the [ts_lister]
script (by default called list_functions.ts) reside in the
base directory alongide the [project_directory] and 
[fuzz_test_directory] folders specified in config.yaml.

[project_directory] should contain projects in this format:

base_dir/
   create_fuzz_tests.py
   run_fuzz_tests.py
   ...
   [project_directory]/
      projectName/
         src/
            fileName.ts
   [fuzz_test_directory]/
   ...

All .ts files in a src folder in this structure that have
an appropriate tsconfig.json will be analyzed for testing.

The created fuzz test files will reside in a folder inside
[fuzz_test_directory] that bears the same name as their
original project. Each file corresponds to one function
and uses fast-check to fuzz it. 

run_fuzz_tests.py runs all tests under [fuzz_test_directory]
and stores all results for each project under projName.log
in that project's folder under [fuzz_test_directory]. An
optional log containing all test results can be created 
directly under [fuzz_test_directory]. (see config)

---Config:
The config.yaml file contains options for file names,test
creation,and test running.
