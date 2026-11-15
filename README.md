# Rex Scrollback Tool

Use the fzf picker to find a command in terminal scrollback. Copy the command, its output, or both. Or open a text snapshot in `$VISUAL`, `$EDITOR`, or `nvim`.

I missed tmux copy mode. I also relied on Snaglord to find and copy commands and their output. The fzf picker follows that Snaglord workflow. The editor mode opens scrollback for broader review. This tool does not select arbitrary screen text or replace tmux copy mode.

Rex runs on macOS. The tool uses macOS `pbcopy` for clipboard access. The CLI can read a saved text capture without Rex. Live pane capture needs the Rex CLI.

## Requirements

- Python 3.9 or newer
- fzf
- macOS `pbcopy` for the interactive picker
- Rex CLI for live pane capture
- An editor on `PATH` for scrollback editing

The tool uses `nvim` if you do not set `$VISUAL` or `$EDITOR`.

## Install

Install the command with uv:

```sh
uv tool install --from git+https://github.com/rvwallace/rex-scrollback-tool rex-scrollback-tool
```

To upgrade:

```sh
uv tool upgrade rex-scrollback-tool
```

## Use with Rex

Browse command history in a Rex pane:

```sh
rex-scrollback browse --session "$REX_SESSION" --block "$REX_BLOCK"
```

Open a text snapshot of pane scrollback in an editor:

```sh
rex-scrollback edit --session "$REX_SESSION" --block "$REX_BLOCK"
```

The editor opens a temporary file. The tool deletes this file after the editor exits. Use `:saveas /path/to/file` in your editor to keep a copy.

Add these commands as Rex palette actions or shortcuts. See the [Rex action example](examples/history.lua).

## Use with a saved capture

Print parsed commands as JSON:

```sh
rex-scrollback preview --input /path/to/capture.txt
```

The default command marker is `CMD>` at the start of a line. The default prompt height is three lines. These lines remove prompt decoration before the next command. Set another marker or prompt height with `--prompt` and `--prompt-lines`:

```sh
rex-scrollback preview --input capture.txt --prompt '^❯ ' --prompt-lines 2
```

The picker searches commands from one pane. It only sees commands that remain in scrollback. It does not read shell history or other panes.

Text matching can mistake prompt-like output for a command. It cannot reliably identify commands that span multiple lines. Use a distinct prompt marker to reduce these errors. The picker never runs the selected command.

The Rex capture API does not return command ranges. A future version can read structured command boundaries if Rex or a shell exposes them.

## Picker keys

| Key | Result |
| --- | --- |
| Enter | Copy output |
| Ctrl+y | Copy command |
| Ctrl+b | Copy prompt line and output |
| Esc | Cancel |
| Ctrl+d / Ctrl+u | Scroll the preview |

## Development

```sh
python -m pip install -e .
rex-scrollback preview --input path/to/capture.txt
```

## License

MIT. See [LICENSE](LICENSE).

OpenAI Codex assisted with the code and documentation. Review the code and test it in your environment before you use it. This project comes as-is and has no warranty. See the license for the full terms.
