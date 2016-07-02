#/bin/sh

# Check for Ubuntu Python3
export pytestcmd="py.test-3"

# Revert to default pytest
if ! type "$pytestcmd" 2> /dev/null; then
    export pytestcmd="py.test"
fi

$pytestcmd --resultlog=/tmp/pytest.log ngtest.py
