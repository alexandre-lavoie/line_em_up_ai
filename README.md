# Line Em' Up AI

AI for Line Em' Up game made for COMP 472.

## Implementation

This AI uses MAX^N to allow more than 2 player games. There is early stopping similar to AlphaBeta implemented aswell. These algorithms call 2 different heuristic.

### Heuristic 1

This simple heuristic tries to optimize having 2 neighbors for each coordinate. This encourages lines to form.

### Heuristic 2

This complex heuristic checks all possible line combination for the last N moves and sees which player has the longest line.

## Running

To run the AI, copy the `__init__.py` and `base.py` into the `line_em_up` repo. This can be done in the main repo by modifying the `.env`:

```
...
AI_PATH=/path/to/this/repo
...
```

and using the following command:

```
python main.py copy
```
