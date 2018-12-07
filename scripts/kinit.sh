#!/usr/bin/env bash

# Get LXPLUS Kerberos ticket
# 
# Requires you to set KRB_USERNAME, KRB_PASSWORD as secure variables
# Should use a CERN Service account: https://account.cern.ch/account/Management/NewAccount.aspx

set +x  # Make sure no variables visible
set -e  # Quit on error

# mostly follwing https://gitlab.cern.ch/gitlabci-examples/kinit_example
mkdir -p ~/.ssh
test -f ~/.ssh/known_hosts || touch ~/.ssh/known_hosts
# validate lxplus's SSH key
grep -q "^lxplus.cern.ch ssh-rsa"  ~/.ssh/known_hosts || echo "lxplus.cern.ch ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAIEAxDFr+wqtWq0sDCGO2LfsMKVwmhsdXC9TYCVq6HoEBEOXFUgc/3Kf2NooJTgHRQ9h7ZEhx8vdZgoy2+XTwJvqYzx9epIC/gC/ts2z47TvK+FAAkpci5V/5zc9pu8fEYCEwrP+FgF7d3k2ivmZ95Mi/Hhmd9xzxAdps6bpJN19EA0=" >> ~/.ssh/known_hosts
# tell SSH to forward Kerberos credentials so lxplus can access AFS/EOS on behalf of the user
echo -e "Host *\n\tGSSAPIDelegateCredentials yes\n\tGSSAPITrustDNS yes\n\n" > ~/.ssh/config
# make sure to get a forwardable Kerberos ticket so lxplus can access AFS/EOS on behalf of the user
echo "${KRB_PASSWORD}" | kinit -f ${KRB_USERNAME}@CERN.CH
