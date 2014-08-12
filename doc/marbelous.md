Marbelous
=========

This document is not a reliable specification of the Marbelous language. The language is in significant flux. This document specifically and only describes the features and dialect of the language implemented by the interpreter found in the same [repository](https://github.com/marbelous-lang/marbelous.py).

Language
--------

Marbelous is a simulation of one or more discrete values ("marbles") moving between positions ("cells") on a two dimensional grid ("board") and interacting with static elements of that grid ("devices"). Devices can alter the value of a marble, produce new marbles, or change the location of a marble. This movement and these actions happen in discrete time increments ("ticks") and all events in a single tick happen simultaneously. Imagine the simulation as a sort of Rube Goldberg marble run.

After the initial board is defined, additional boards may be named and defined. Any board may be placed as a device on a board, called a "function". This is the only type of device that may be more than one cell wide. When the defined inputs for a function are filled, the board in question is queued to be run. The next time the parent board would tick, the sub-board ticks instead. The input marbles are transferred to the new board. The new board is run to completion within a single tick of its parent board. Finally the outputs, if any, of the function appear below or beside the function device. In practice, this means that appropriately built functions may precisely replicate the behavior of most predefined devices.

Marbles are represented by a two digit hexadecimal number, uppercase, allowing values from 0 to 255 (0x00 to 0xFF). All mathematical operations in Marbelous are modulo 256. Devices are represented by two characters that are not a valid marble. Many predefined devices are described below. Function devices wider than one cell may have proportionally longer names. Empty space on the board may be considered to be a device that simply allows the marble to fall downwards.

A marbelous program is executed by repeatedly performing two alternating steps:
1) All marbles undergo the actions specified by the device in their cell, and all functions execute if their inputs are filled.
2) All overlapping marbles are added together.

Any marble that falls off the bottom of a board is written to STDOUT. If multiple marbles leave a board at the same time step, they are written from left to right. If multiple marbles leave multiple boards (simultaneous function execution) at the same time step, the output order is undefined.

Command line arguments need to be single byte-sized integers and are fed to the main board’s input cells.

The execution of any Board is terminated when no marbles are moving, all explicit outputs are filled, or any board terminator is filled.

Devices
-------

* `\/` is a trash bin, which just removes all marbles.
* `/\` is a cloner, which splits any marble and places two identical copies in the cell to its left and to its right.
* `\\` and 
* `//` are deflectors which displace any marble one cell to the right or left, respectively.
* `++` increments the marble on it and lets it fall through
* `--` decrements the marble on it and lets it fall through
* `+n` adds n to the marble
* `-n` subtracts n from the marble
* `>>` shifts bits right (divide by two)
* `<<` shifts bits left (multiply by two)
* `^n` returns 1 if the nth bit of the marble is 1 and 0 if it's 0. Where `^0` is the least significant bit. 
* `~~` invert bits (binary not)
* `=n` lets marbles equal to n fall through, sends others to the right
* `>n` lets marbles greater than to n fall through, sends others to the right
* `<n` lets marbles less than to n fall through, sends others to the right
* `@n` is a portal, which transports a marble to the cell beneath a random other portal with the same n
* `&n` is a synchroniser, which stalls a marble until there is a marble on every synchroniser with the same n, when they all fall through
* `?n` generates a random marble 0-n
* `??` generates a random marble 0 through the value of the input marble
* `!!` return from the current board immediately
* `}n` will contain the n-th input when a function is invoked. Duplicates of the same `}n` result in duplicated input values.
* `{n` act like a group of synchronisers to collect the outputs. The function terminates when all outputs are filled with a marble (or the termination device, `!!`, is used). Each {n may be used multiple times, and only one of each n needs to be filled for the function to terminate. If multiple cells are filled, the marbles will be added to give the output.
* `{<` and ...
* `{>` are additional outputs which appear to the sides of the function device. If present, these need to be filled too, for the board to terminate. They have no effect on the main board.
* `]]` reads one byte from stdin which falls, or outputs the input marble to the right

Any device whose defined name ends with "n" actually has 36 variations, from `_0` to `_Z`
With the exception of `^n`, which has 8 variations, form `^0` to `^7`.

Functions
---------

The number of inputs and outputs of a cell is implicitly determined by the distinct `}n` and `{n` used.

To use a board as a function, you write its name across max(1,I+1,O+1) horizontally adjacent cells. Where I is the highest input number used and O is the highest output number used (side outputs are not counted). If the board's name is not as long as its device width, the name is repeated.

The main board has the name "MB", to be repeated across as many cells as the main board has inputs.

Misc
----

Comments in a board file begin with `#`

Additional mbl files may be included with `#include file.mbl`, which ignores the main board in the included file.

The interpreter has various levels of verbosity and different output behaviors, lightly explained in `marbelous.py --help`

Examples
--------

    # prints out "Hello, world!"
    48 65 6C 6C 6F 2C 20 77 6F 72 6C 64 21

    # {0 = }0 + }1
    }0 .. }1
    \\ {0 //

    # {0 = }0 * }1
    # masks out bits of }1
    # shifts copies of }0 left that many times
    # sums shifted copies
    .. }1 }1 }1 }1 }1 }1 }1 }1
    00 ^7 ^6 ^5 ^4 ^3 ^2 ^1 ^0
    .. =1 =1 =1 =1 =1 =1 =1 =1
    .. &7 &6 &5 &4 &3 &2 &1 &0
    .. }0 .. .. .. .. .. .. ..
    .. &7 }0 .. .. .. .. .. ..
    .. << &6 }0 .. .. .. .. ..
    .. << << &5 }0 .. .. .. ..
    .. << << << &4 }0 .. .. ..
    .. << << << << &3 }0 .. ..
    .. << << << << << &2 }0 ..
    .. << << << << << << &1 }0
    .. << << << << << << << &0
    {0 // // // // // // // //

    # calculates the nth fibonacci number, recursively.
    :Fb
    }0 }0 }0 .. # three copies of }0, call them A B C
    -- &0 >1 {0 # decrement A, hold B for sync, return C if it's <2
    &0 -- >4 -- # hold A for sync, decrement B, divert and decrement C if it's <5
    -- Fb &0 {0 # decrement A, recurse with B, release sync or return C-1
    Fb .. \/ .. # recurse with A, do nothing with B, trash C
    \\ {0 .. .. # add A to B and return it


Additional examples are available in the [examples directory](https://github.com/marbelous-lang/marbelous.py/tree/master/examples).
