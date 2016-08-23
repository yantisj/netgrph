#/bin/sh

# Check for Ubuntu Python3
export pytestcmd="py.test-3"

# Revert to default pytest
if ! type "$pytestcmd" 2> /dev/null; then
    export pytestcmd="py.test"
fi

if [ "$1" = "prod" ]; then
    $pytestcmd --resultlog=/tmp/pytest.log -k test_prod ngtest.py
else
    $pytestcmd --resultlog=/tmp/pytest.log -k test_dev ngtest.py
fi

