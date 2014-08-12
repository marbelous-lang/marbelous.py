Marbelous examples
==================

Marbelous files in this directory are examples of what can be done with the language.

The standard format for an example includes a main board that accepts one or more inputs and outputs results to stdout. A sub-board should provide the demonstrated functionality, so that the example might be included in another mbl file.

If the function in question returns numeric results then the main board can #include dec_out.mbl and send one marble to the Dp function then send its three-marble output to stdout