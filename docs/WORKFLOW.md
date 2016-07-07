# All development done on the dev branch

# For release to master, checkout master, advance version, then pull from dev with no fast forward
```
edit docs/VERSION
git tag v0.7.x
git merge --no-ff --log origin/dev
git push origin master
```
