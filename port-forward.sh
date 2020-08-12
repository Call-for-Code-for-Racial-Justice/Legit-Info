#!/bin/bash
sudo systemctl stop postgresql-10
echo "We will port forward 5432, do not close this terminal"
oc port-forward service/fixpolsvc 5432:5432
