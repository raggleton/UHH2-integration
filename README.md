# UHH2-integration

This repository is designed to run integration tests for UHH2 code: https://github.com/UHH2/UHH2.
One can test PRs, or any personal branch, provided it is on github.
To perform a test of a PR or branch, one should commit this as an individual branch, and then gitlab-CI will then run the tests against it.

## Setup

The best way to run this is to fork your own copy of this repository. This is for security reasons: for proper testing, this involes interacting with the NAF via SSH, which requires your personal credentials and thus should remain private.

But if you just want to quickly test if a PR compiles, then one can use the main UUH2 copy of the repo.

### Personal setup

To add in your DESY credentials for logging onto the NAF:

**TODO**

## Usage

### 1: I have a new Pull Request to UHH2 that I want to test

Simply: edit `to_test.sh` to ensure (1) the PR number, and (2) the reference branch are both correct.

Commit this to a new branch, then push to gitlab:

```
git checkout -b testXXX
nano to_test.sh
...
git add to_test.sh
git commit -m "Test PR XXX"
git push origin testXXX
```

Then watch the jobs run

### 2: The Pull Request has been updated, I want to re-run the jobs

In the gitlab CI/CD Pipelines page, click the "Run Pipeline" button. 
Then on the next page select the branch you want to run (`textXXX`), then "Create Pipeline".

Note that the retry button next to each pipeline in the table **only** reruns failed jobs, and thus will not pick up the latest code changes (which happens in the "getit" stage, which normally succeeds).

### 3: I made changes to this integration code, and want to re-run a job withmy new changes

In this case, we will merge the changes into the PR branch and then push:

```
git checkout testXXX
git merge master
git push origin testXXX
```

### 4: I want to test my own private branch that isn't a Pull Request

Edit `to_test.sh` and replace:

- `REMOTENAME` - your github username
- `REMOTEBRANCH` - branch name on your copy of UHH2 repo you want to test
- `REFBRANCH` - the reference branch for your branch (e.g. RunII_94X_v2)

Then follow as per "1: I have a new Pull Request to UHH2 that I want to test"

## What this tests

- The modified code merges with the reference branch
- The modified code deploys & compiles successfully *exactly* like a user would (using same install script)

### Future tests yet to be implemented

- Test the diff for spurious `couts`
- XML ROOT file existence (& empty?) checker
- Run over data & MC to make small ntuples:
    - Ntuple size checker
    - Ntuple contents tests (empty branches, duplicate branches, store trig & MET flags etc)
- pylint checker
- Create CRAB tarball & check size
- clang-tidy / scram b code-checks
