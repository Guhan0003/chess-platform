# Chess Piece Sets

Place chess piece images in subfolders here. Each piece set should have its own folder.

## Folder Structure

```
pieces/
├── classic/
│   ├── wK.png  - White King
│   ├── wQ.png  - White Queen
│   ├── wR.png  - White Rook
│   ├── wB.png  - White Bishop
│   ├── wN.png  - White Knight
│   ├── wP.png  - White Pawn
│   ├── bK.png  - Black King
│   ├── bQ.png  - Black Queen
│   ├── bR.png  - Black Rook
│   ├── bB.png  - Black Bishop
│   ├── bN.png  - Black Knight
│   └── bP.png  - Black Pawn
├── modern/
│   └── (same 12 files)
├── staunton/
│   └── (same 12 files)
├── neo/
│   └── (same 12 files)
└── alpha/
    └── (same 12 files)
```

## File Naming Convention

- First letter: `w` for white, `b` for black
- Second letter: Piece type (uppercase)
  - `K` = King
  - `Q` = Queen
  - `R` = Rook
  - `B` = Bishop
  - `N` = Knight
  - `P` = Pawn

## Image Specifications

- **Format**: PNG with transparency (recommended), SVG, or JPG
- **Size**: 100x100 to 200x200 pixels (will be scaled to fit)
- **Background**: Transparent (for PNG/SVG)

## Adding a New Piece Set

1. Create a new folder with your set name (lowercase, no spaces)
2. Add all 12 piece images with the naming convention above
3. Register the set in `frontend/src/utils/theme-config.js`:

```javascript
{
  id: 'your-set-name',
  name: 'Display Name',
  folder: 'your-set-name'
}
```

## Fallback

If images are not found, the system will fall back to Unicode chess symbols:
♔ ♕ ♖ ♗ ♘ ♙ (white) and ♚ ♛ ♜ ♝ ♞ ♟ (black)
