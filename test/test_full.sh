#/bin/sh
export pytestcmd="py.test-3"

if ! type "$pytestcmd" 2> /dev/null; then
    export pytestcmd="py.test"
fi

$pytestcmd --resultlog=/tmp/pytest.log ngtest.py
