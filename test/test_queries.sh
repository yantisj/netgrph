#/bin/sh

export pytestcmd="py.test-3"

if ! type "$pytestcmd" 2> /dev/null; then
    export pytestcmd="py.test"
fi

if [ "$1" = "prod" ]; then
    $pytestcmd --resultlog=/tmp/pytest.log ngtest.py::test_prod_queries
else
    $pytestcmd --resultlog=/tmp/pytest.log ngtest.py::test_dev_queries
fi
