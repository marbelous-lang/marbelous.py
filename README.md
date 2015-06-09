marbelous.py
============

Python interpreter for Marbelous

Marbelous is an esoteric programming language based on numbered marbles falling down a Rube Goldberg like board full of devices that move and manipulate the marbles.

Creation of this language was inspired by conversation in the Programming Puzzles & Code Golf StackExchange [chat room](http://chat.stackexchange.com/rooms/240/the-nineteenth-byte), forked to a [dedicated chat room](http://chat.stackexchange.com/rooms/16230/marbelous-esolang-design) later.

Credit for the original idea goes to cjfaure.
Additional language design input from Martin Büttner, Nathan Merrill, overactor, sparr, githubphagocyte, es1024, VisualMelon.

First versions of interpreter by sparr.

Example program (more in examples/):

    # calculates the nth fibonacci number, recursively
    }0 }0 }0 .. # three copies of }0, call them A B C
    -- &0 >1 {0 # decrement A, hold B for sync, return C if it's <2
    &0 -- >4 -- # hold A for sync, decrement B, divert and decrement C if it's <5
    -- Fb &0 {0 # decrement A, recurse with B, release sync or return C-1
    Fb .. \/ .. # recurse with A, do nothing with B, trash C
    \\ {0 .. .. # add A to B and return it
