# Style Guidelines

## Character Set

This project uses UTF-8.

## PEP 8 Style Guide for Python
This project adheres to the [PEP 8 Style Guide for Pyton 
Code](https://www.python.org/dev/peps/pep-0008/).  PEP — short for Python 
Enhancement Proposal — is a list of documents that propose new features or 
conventions for the Python programming language. Of these, PEP 8, is a living
document of style conventions for writing Python

Here is a brief summary, based in part [A Five-Minute Introduction to Python's 
Style Guide PEP 8](https://medium.com/code-85/a-five-minute-introduction-to-pythons-style-guide-pep-8-57202886265f)
by Jonathan Hsu.

**Naming Conventions**

Different programming languages have different conventions for upper case (A-Z)
and lower case (a-z) characters used in identifiers.

* For functions, class methods, and variables, use snake case (lowercase 
letters and underscores to separate words).
* For classes, use CapWords [
CamelCase](https://en.wikipedia.org/wiki/Camel_case): capitalize the first 
letter of each word.
* For constants, use all capital letters and underscores to separate words.
* Avoid using overly abbreviated names such as fn; write out first_name 
instead.
* All identifiers must be in ASCII only, using English words.

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

**Comments**

* Comments that contradict the code are worse than no comments. Always make a
priority of keeping the comments meaningful and up-to-date when the code
changes!
* Comments should be complete sentences. 
* Use triple-doublequotes """ to write docstrings for all public modules,
functions, classes, and methods.


## Django Conventions

## Markdown Conventions

