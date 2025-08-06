
# typescript_fuzzer

## Purpose:
Fuzz test TypeScript Projects by extracting their functions and using fast-check to fuzz them.

## Dependencies:
This tool is meant for use in bash. You will need to be able to run Python and TypeScript files. Please install the following packages:  

Dependencies:  
- fast-check
- jest
- ts-jest
- ts-morph

Install with `npm install fast-check jest ts-jest ts-morph`
  
devDependencies:  
- @types/jest
- @types/mock-require
- @types/node
- mock-require
- ts-node
- typescript

Install with `npm install --save-dev typescript ts-node mock-require @types/node @types/mock-require @types/jest`

## Instructions:
1. Place all TypeScript programs to be analyzed in the \[programs\] folder. Only .ts files under \[programs\]/foo/src/ and any subdirectories of src will be analyzed. All programs without a src folder or valid tsconfig.json will be skipped.  
2. Execute create_fuzz_tests.py with `python3 create_fuzz_tests.py`.  
3. Execute run_fuzz_tests.py with `python3 run_fuzz_tests.py`.
4. Check the generated logs for each program under \[fuzz_test_directory\]/foo/foo.log

## Expected Input/Output:  
### Input:  
Any number of .ts files under \[programs\]/foo/src/ or any of src's subdirectories.  
### Output:  
After create_fuzz_tests.py, one fuzz test file for each exportable function in \[fuzz_test_directory\]/foo in the format bar_fuzz.test.ts.  
After run_fuzz_tests.py, one log file for each project stored in \[fuzz_test_directory\]/foo/foo.log.  
An optional log file containing results from all tests run can be created under \[fuzz_test_directory\]/.  

## Expected File Structure:
create_fuzz_tests.py, run_fuzz_tests.py, and the \[ts_lister\] script reside in the base directory alongide the \[project_directory\] and \[fuzz_test_directory\] folders specified in config.yaml.

## Config:
The config.yaml file contains options for file and directory names, test creation, and test running.
