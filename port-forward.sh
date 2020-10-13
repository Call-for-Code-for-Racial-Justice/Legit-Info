#!/bin/bash
sudo systemctl stop postgresql-10
echo "Use 'icc embrace' to log into IBM Cloud and OpenShift"
iccheck
echo "We will port forward 5432, do not close this terminal"
oc port-forward service/cfcappdb 5432:5432
