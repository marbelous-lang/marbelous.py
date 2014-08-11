Marbelous
=========

This document is not a reliable specification of the Marbelous language. The language is in significant flux. This document specifically and only describes the features and dialect of the language implemented by the interpreter found in the same [repository](https://github.com/marbelous-lang/marbelous.py).

Language
--------

Marbelous is a simulation of one or more discrete values ("marbles") moving between positions ("cells") on a two dimensional grid ("board") and interacting with static elements of that grid ("devices"). Devices can alter the value of a marble, produce new marbles, or change the location of a marble. This movement and these actions happen in discrete time increments ("ticks") and all events in a single tick happen simultaneously. Imagine the simulation as a sort of Rube Goldberg marble run.

After the initial board is defined, additional boards may be named and defined. Any board may be placed as a device on a board, called a "function". This is the only type of device that may be more than one cell wide. When the defined inputs for a function are filled, the board in question is instanciated. The input marbles are transferred to the new board. The new board is run to completion as a single action, in a single tick, of the board on which the function device is found. Finally the outputs, if any, of the function appear below or beside the function device. In practice, this means that appropriately built functions may precisely replicate the behavior of most predefined devices.

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
* `!!` invert bits (binary not)
* `=n` sends marbles equal to n to the right, others down
* `>n` sends marbles greater than to n to the right, others down
* `<n` sends marbles less than to n to the right, others down
* `Pn` is a portal, which transports a marble to the cell beneath a random other portal with the same n
* `Sn` is a synchroniser, which stalls a marble until there is a marble on every synchroniser with the same n, when they all fall through
* `Rn` generates a random marble 0-n
* `R?` generates a random marble 0 through the value of the input marble
* `XX` return from the current board immediately
* `In` will contain the n-th input when a function is invoked. Duplicates of the same `In` result in duplicated input values.
* `On` act like a group of synchronisers to collect the outputs. The function terminates when all outputs are filled with a marble (or the termination device, `XX`, is used). Each On may be used multiple times, and only one of each n needs to be filled for the function to terminate. If multiple cells are filled, the marbles will be added to give the output.
* `O<` and
* `O>` are additional outputs which appear to the sides of the subroutine device. If present, these need to be filled too, for the subroutine to terminate. They have no effect on the main board.

Any device whose defined name ends with "n" actually has 36 variations, from `_0` to `_Z`

Functions
---------

The number of inputs and outputs of a cell is implicitly determined by the distinct `In` and `On` used.

To use a subroutine, you write its name across max(1,I+1,O+1) horizontally adjacent cells. Where I is the highest input number used and O is the highest output number used (side outputs are not counted). If the function's name is not as long as its device width, the name is repeated.

The main board is just another subroutine with the identifier MB, to be repeated across as many cells as the main board has inputs.

Misc
----

Comments in a board file begin with `#`

Additional mbl files may be included with `#include file.mbl`

The interpreter currently only has a "verbose" mode. The board state is printed to stdout at every tick. Marble output meant for stdout is queued until the program completes, and is displayed along with any outputs of the main board.

Examples
--------

    # prints out "Hello, world!"
    48 65 6C 6C 6F 2C 20 77 6F 72 6C 64 21

    # adds together two numbers
    I0 .. I1
    \\ .. //
    .. O0 ..

    # O0 = I0 * I1
    # loops I0 times, adding I1 to itself
    I0 P0 .. P1 I1 .. # two inputs, tops of both portal loops
    \\ >0 S0 \\ S0 .. # if I0>0, release I1 from S0
    .. S1 -- 00 /\ P1 # if I0=0, release S1. send I1 to sum and top
    .. \/ P0 S1 .. .. # trash or loop I0--. sum accumulates on on S1.
    .. .. .. O0 .. .. # output the sum

    # calculates the nth fibonacci number, recursively
    I0 I0 I0 .. # three copies of I0, call them A B C
    -- S0 <2 O0 # decrement A, sync B, return C if <2
    S0 -- <5 -- # sync A, decrement B, divert and decrement C if <5
    -- MB S0 O0 # decrement A, recurse B, release sync or return C-1
    MB .. \/ .. # recurse A, B falls, trash C
    \\ O0 .. .. # return A+B

Additional examples are available in the [examples directory](https://github.com/marbelous-lang/marbelous.py/tree/master/examples).