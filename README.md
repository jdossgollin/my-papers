# my-papers

This repository contains a bibtex (`.bib`) file containing my papers.

* `my-papers.bib`: papers by me.
* `library.bib`: my library, exported from Zotero using Better Bibtex

## To use

The easiest way to use this in a project is as a [`git` submodule](https://www.vogella.com/tutorials/GitSubmodules/article.html)

To install this in your project:

```
git submodule add -b master https://github.com/jdossgollin/my-papers.git
git submodule init 
```

To pull the latest changes from my repository to the project

```
git submodule update
cd my-papers
git pull
cd ..
```

To remove from your document

```
# Remove the submodule entry from .git/config
git submodule deinit -f my-papers

# Remove the submodule directory from the superproject's .git/modules directory
rm -rf .git/modules/my-papers

# Remove the entry in .gitmodules and remove the submodule directory located at path/to/submodule
git rm -f my-papers
```