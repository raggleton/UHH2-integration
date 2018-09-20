# Only set variables in here to get UHH2 from github

# To test a PR, ensure that REMOTENAME is UHH2, set the PR number in PRNUM, 
# and ensure REMOTEBRANCH has the form: pull/${PRNUM}/head
# 
# You should then set REFBRANCH to the reference version you are working on, 
# e.g. RunII_94X_v2
#
# Alternatively, you can set REMOTENAME and REMOTEBRANCH to your 
# username & branchname to test your branch, along with setting REFBRANCH

export REMOTENAME="UHH2"
export PRNUM=1008
export REMOTEBRANCH=pull/${PRNUM}/head
export REFBRANCH="RunII_94X_v2"

# Local branchname on testmachine, you shouldn't need to touch this
export LOCALBRANCH="test$PRNUM"