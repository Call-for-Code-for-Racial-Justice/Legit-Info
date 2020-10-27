# Style Guidelines

## Contents

1. [General Guidance](#general-guidance)
1. [Character Set](#character-set)
1. [Python Style Guide](#python-style-guide)


## General Guidance

> "Build tools for others that you want to be built for you." 
> -- <cite>Kenneth Reitz</cite>

> "Simplicity is alway better than functionality." 
> -- <cite>Pieter Hintjens</cite>

> "Fit the 90% use-case. Ignore the nay sayers." 
> -- <cite>Kenneth Reitz</cite>

> "Readability counts. Beautiful is better than ugly.  Explicit is better 
> than implicit. Fix each broken window (bad design, wrong decision, or poor 
> code) as soon as it is discovered.  Now is better than never." 
> -- <cite>PEP 20</cite>

> Test ruthlessly. Write docs for new features.

## Character Set

This project uses UTF-8 character set, the default for Python and HTML5,
except Python identifiers (variables, methods, functions) that should be
written in 7-bit ASCII, a subset of UTF-8.  See [UTF-8
](https://en.wikipedia.org/wiki/UTF-8) in Wikipedia for details.

the following terminology is used in the rest of this document:

* UTF-8: a multi-byte character representation based on Unicode.  Most
characters use only a single byte.
* ASCII: refers to the 7-bit standard. For compatability, the first 128 
characters of UTF-8 is identical to ASCII.

Capitalization methods are defined as follows:

* Uppercase -- Letters in ABCDEFGHIJKLMNOPQRSTUVWXYZ
* Lowercase -- Letters in abcdefghijklmnopqrstuvwxyz
* TitleCase -- In the United States, titles capitalize the first and last
words, and capitalize all other words unless they are one of
a handleful of stopwords (a, an, and, at, but, by, for, in, nor, of, on, or,
so, the, to, up, yet).
* SentenceCase -- Statements that have uppercase as the first word in a
standard english sentence, other words start with lower case letters unless
they are formal names or acronyms.  Full UTF-8 character set supported to
handle foreign names and words with international characters. The sentence 
ends with a period.
* SnakeCase -- lowercase ASCII characters with words separated by underscore.
Example: this_function_name
* [CamelCase
](https://en.wikipedia.org/wiki/Camel_case) -- multiple words combined without 
spaces, first character is lowercase ASCII, and subsequent words start with
uppercase ASCII letter.  Example:  thisFunctionName
* CapWords -- often called PascalCase or upper CamelCase -- all words start 
with uppercase, with no spaces in between.  Example:  ThisFunctionName
* Kebab-case -- similar to SnakeCase, but with words separated by hyphens, 
used for file names, object names, and command line parameters.


## Python Style Guide
This project adheres to the [PEP 8 Style Guide for Pyton 
Code](https://www.python.org/dev/peps/pep-0008/).  PEP — short for Python 
Enhancement Proposal — is a list of documents that propose new features or 
conventions for the Python programming language. Of these, PEP 8, is a living
document of style conventions for writing Python

Here is a brief summary, based in part [A Five-Minute Introduction to Python's 
Style Guide PEP 8
](https://medium.com/code-85/a-five-minute-introduction-to-pythons-style-guide-pep-8-57202886265f)
by Jonathan Hsu.

**Naming Conventions**

Different programming languages have different conventions for upper case (A-Z)
and lower case (a-z) characters used in identifiers.

* For functions, class methods, and variables, use snake case (lowercase 
letters and underscores to separate words).
* For classes and API methods, use CapWords [
: capitalize the first 
letter of each word.
* For constants, use all capital letters and underscores to separate words.
* Avoid using overly abbreviated names such as fn; write out first_name 
instead.
* All identifiers must be in 7-bit ASCII only, using English words.

**Indentation**

Since Python uses indentation in lieu of curly braces to denote block
ownership, it is critical to have clean and consistent indentation style.

* Use exactly four (4) spaces per indentation level.  This often
can be set as the default in your text editor.
* For longer lists of values, either indent based on the opening delimiter or
use a hanging indent. 
* For multiline constructs, the closing symbol can be aligned with the used
whitespace or with the first character of the statement.

**Whitespace and Line Breaks**

White space and line breaks can greatly help the readability of Python code.

* Use two blank lines for top-level function/class definitions and one blank
line for method definitions.
* Use whitespace around assignment and logical operators.  Avoid excessive
whitespace immediately inside of parenthesis, brackets, or braces.
* Blank lines should contain no spaces.  Avoid trailing whitespace anywhere.
* Keep lines under 79 characters — this is intended to minimize line-wrapping
on side-by-side windows.

**Single Quotes or Double Quotes**

* Use double quotes for strings with an apostrophe.
* Use single quotes for strings with quotation marks.
* Always use parentheses with double quotes for multiline strings.

**Imports**

Put all imports at the top of the page with three sections, each separated by
a blank line, in this order:

1. System imports
1. Third-party imports, including Django imports
1. Local source tree imports from this application

**Comments**

* Comments that contradict the code are worse than no comments. Always make a
priority of keeping the comments meaningful and up-to-date when the code
changes!
* Comments should be complete sentences in SentenceCase capitalization. 
* Use triple-doublequotes """ to write docstrings for all public modules,
functions, classes, and methods.

To check your code for consistency to these guidelines, use the 
[flake8](https://pypi.org/project/flake8/) utility.  Any code that results
in flake8 errors prevents the application from being deployed on IBM Cloud.

```console
$ flake8  my_program.py
```

To better understand guideline violates flagged by flake8, use the 
[pycodestyle](https://github.com/PyCQA/pycodestyle) utility.

```console
$ pycodestyle  --show-source  --show-pep8  my_program.py
```


Many guideline violations flagged by flake8 can be automatically corrected
using [autopep8](https://pypi.org/project/autopep8) utility.  For example:

```console
$ autopep8  --in-place  my_program.py
```



## Django Conventions

## Markdown Conventions

