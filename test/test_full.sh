#/bin/sh
export pytestcmd="py.test"

if ! type "$pytestcmd" 2> /dev/null; then
    export pytestcmd="py.test-3"
fi

$pytestcmd --resultlog=/tmp/pytest.log ngtest.py
