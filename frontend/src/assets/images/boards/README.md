# Board Themes

Place board textures/colors in subfolders here. Each theme should have its own folder.

## Folder Structure
   
```
boards/
├── classic/
│   ├── light.png (or light.jpg) - Light square texture
│   └── dark.png (or dark.jpg)   - Dark square texture
├── wood/
│   ├── light.png
│   └── dark.png
├── marble/
│   ├── light.png
│   └── dark.png
├── green/
│   ├── light.png
│   └── dark.png
└── blue/
    ├── light.png
    └── dark.png
```

## Notes

- Images can be PNG, JPG, or SVG format
- Recommended size: 100x100 pixels (will be scaled to fit square)
- If no image is provided, CSS fallback colors will be used
- You can also use solid colors by not providing images (see theme-config.js)

## Color-Only Themes

If you only want solid colors (no texture), don't add images. Instead, define the colors in:
`frontend/src/utils/theme-config.js`

Example:
```javascript
{
  id: 'ocean',
  name: 'Ocean Blue',
  lightColor: '#e8f4f8',
  darkColor: '#4a90a4',
  hasTexture: false
}
```
