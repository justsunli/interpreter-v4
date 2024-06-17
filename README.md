# Brewin# Interpreter

A quarter-long project for CS 131 - Programming Languages. This project is the final version of a Brewin interpreter that provides supports in some enhanced features of previous Brewin#. 

## Key Features

- [x] **Object Support:** Brewin# introduces objects that can have their own fields and methods without the use of classes.
- [x] **Prototypal Inheritance:** Objects can inherit from prototype objects, allowing for method and field inheritance across multiple levels.
- [x] **Enhanced Object Operations:** Objects in Brewin# can be passed as parameters, returned from functions, and compared for equality.
- [x] **Dynamic Object Management:** Fields and methods can be dynamically added to objects, and the 'this' keyword is supported within methods for referring to the object itself.

## Setup and Execution

1. Clone the repository to your local machine.
2. Ensure Python is installed and navigate to the project directory.
3. Run the interpreter using a Brewin# program file as input.

## Usage Example

```python
# Example of defining and manipulating objects#

def main() {
    a = @;  # Creates a new object
    a.x = 10;  # Adds field 'x' with value 10
    print(a.x);  # Outputs: 10
}
```

## Licensing and Attribution

This is an unlicensed repository; even though the source code is public, it is **not** governed by an open-source license.

This code was primarily written by [Carey Nachenberg](http://careynachenberg.weebly.com/), with support from his TAs for the [Fall 2023 iteration of CS 131](https://ucla-cs-131.github.io/fall-23-website/).
