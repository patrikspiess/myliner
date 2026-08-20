# Myliner VS Code Extension

Myliner adds a small, collapsible Webview to the Explorer. The view is transparent and frameless,
starts automatically, and uses the same `<myliner-overlay>` component as the browser demo. It does
not replace the Explorer, open an editor tab, stop on click, or register keyboard shortcuts.

The initial settings are two lines, speed `10`, thickness `1`, and endpoint offsets from `1` to
`10` pixels. Four view title buttons control line count and speed. The same actions and
`Myliner: Show Panel` are available from the Command Palette.

Install the source locally on Linux:

```bash
mkdir -p ~/.vscode/extensions/myliner-vscode
rsync -a ./ ~/.vscode/extensions/myliner-vscode/
```

Reload VS Code and expand Myliner in the Explorer.
