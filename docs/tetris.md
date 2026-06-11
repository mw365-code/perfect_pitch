# Tetris Shapes and Colors

Tetris uses 7 tetromino shapes (pieces made from 4 blocks). In modern Guideline-style Tetris, each shape has a standard color:

- **I** (straight line): **Cyan**
- **O** (square): **Yellow**
- **T** (T-shape): **Purple**
- **S** (right-leaning zigzag): **Green**
- **Z** (left-leaning zigzag): **Red**
- **J** (left L-shape): **Blue**
- **L** (right L-shape): **Orange**

These colors are standard in most current versions, though some older or custom Tetris variants may use different palettes.

## Note Order Assignment

Assign tetrominoes in note order `C D E F G A B` using the standard shape/color sequence:

| Note | Shape | Color |
| --- | --- | --- |
| C | Straight line | Cyan |
| D | Square | Yellow |
| E | T-shape | Purple |
| F | Right-leaning zigzag | Green |
| G | Left-leaning zigzag | Red |
| A | Left L-shape | Blue |
| B | Right L-shape | Orange |

## Sharp Note Assignment (Same Shape, Lighter Color)

Sharps use the same shape family as their natural-note base, with a lighter version of the color:

| Sharp Note | Shape (same family) | Color (lighter variant) |
| --- | --- | --- |
| C# | Straight line | Light cyan |
| D# | Square | Light yellow |
| F# | Right-leaning zigzag | Light green |
| G# | Left-leaning zigzag | Light red |
| A# | Left L-shape | Light blue |

## Shape Diagrams (4 Tiles Each)

```text
C (Cyan) - Straight line
[] [] [] []
```

```text
C# (Light cyan) - Straight line
[] [] [] []
```

```text
D (Yellow) - Square
[] []
[] []
```

```text
D# (Light yellow) - Square
[] []
[] []
```

```text
E (Purple) - T-shape
   []
[] [] []
```

```text
F (Green) - Right-leaning zigzag
   [] []
[] []
```

```text
F# (Light green) - Right-leaning zigzag
   [] []
[] []
```

```text
G (Red) - Left-leaning zigzag
[] []
   [] []
```

```text
G# (Light red) - Left-leaning zigzag
[] []
   [] []
```

```text
A (Blue) - Left L-shape
[]
[] [] []
```

```text
A# (Light blue) - Left L-shape
[]
[] [] []
```

```text
B (Orange) - Right L-shape
      []
[] [] []
```
