# Only set variables in here to get UHH2 from github

# To test a PR, ensure that REMOTENAME is UHH2, set the PR number in PRNUM, 
# and ensure REMOTEBRANCH has the form: pull/${PRNUM}/head
#
# Alternatively, you can set REMOTENAME and REMOTEBRANCH to your 
# username & branchname to test your branch

export REMOTENAME="UHH2"
export PRNUM=1011
export REMOTEBRANCH=pull/${PRNUM}/head

# Local branchname on testmachine, you shouldn't need to touch this
export LOCALBRANCH="test$PRNUM"