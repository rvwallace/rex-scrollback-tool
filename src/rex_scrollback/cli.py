#!/usr/bin/env python3
"""Browse commands captured in a Rex pane or a saved terminal capture."""

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile


def parse_blocks(text, prompt=r"^CMD>\s?", prompt_lines=3):
    """Parse prompt-marked commands and the output that follows each command."""
    lines = text.splitlines()
    pattern = re.compile(prompt)
    marks = [(i, pattern.match(line)) for i, line in enumerate(lines)]
    marks = [(i, match) for i, match in marks if match]
    blocks = []
    for n, (start, match) in enumerate(marks):
        command = lines[start][match.end():]
        if not command.strip():
            continue
        end = len(lines)
        if n + 1 < len(marks):
            end = max(start + 1, marks[n + 1][0] - (prompt_lines - 1))
        output = "\n".join(lines[start + 1:end]).rstrip("\n")
        blocks.append({"command": command, "output": output, "prompt_line": lines[start]})
    return blocks


def payload(block, kind):
    if kind == "command":
        return block["command"]
    if kind == "output":
        return block["output"]
    return block["prompt_line"] + ("\n" + block["output"] if block["output"] else "")


def clean_label(text):
    return "".join(c if c.isprintable() else " " for c in text)


def editor_command(capture):
    editor = shlex.split(os.environ.get("VISUAL") or os.environ.get("EDITOR") or "nvim")
    if not editor:
        raise ValueError("The selected editor command is empty")
    options = ["-c", "setlocal nospell"] if Path(editor[0]).name in ("nvim", "vim") else []
    return [*editor, *options, str(capture)]


def run_picker(blocks, folder):
    if not shutil.which("fzf"):
        raise FileNotFoundError("fzf is required; install it and make sure it is on PATH")
    if not Path("/usr/bin/pbcopy").exists():
        raise FileNotFoundError("macOS pbcopy is required to copy a selection")
    rows = []
    for index, block in reversed(list(enumerate(blocks))):
        preview_text = "".join(
            c if c.isprintable() or c in "\n\t" else " " for c in payload(block, "both")
        )
        (folder / str(index)).write_text(preview_text, encoding="utf-8")
        rows.append(f"{index}\t{clean_label(block['command'])}")
    preview = f"/bin/cat {shlex.quote(str(folder))}/{{1}}"
    env = os.environ.copy()
    env.pop("FZF_DEFAULT_OPTS", None)
    env.pop("FZF_DEFAULT_OPTS_FILE", None)
    result = subprocess.run(
        [
            "fzf", "--no-sort", "--layout=reverse", "--delimiter=\t", "--with-nth=2..",
            "--prompt=Commands> ",
            "--header=Enter: output | Ctrl-y: command | Ctrl-b: both | Esc: cancel",
            "--expect=enter,ctrl-y,ctrl-b", "--preview", preview,
            "--preview-window=right,60%,wrap",
            "--bind=ctrl-d:preview-half-page-down,ctrl-u:preview-half-page-up",
        ],
        input="\n".join(rows), text=True, stdout=subprocess.PIPE, env=env,
    )
    if result.returncode in (1, 130):
        return
    result.check_returncode()
    lines = result.stdout.splitlines()
    if len(lines) < 2:
        return
    key, selection = lines[:2]
    index = int(selection.split("\t", 1)[0])
    kind = {"enter": "output", "ctrl-y": "command", "ctrl-b": "both"}[key]
    subprocess.run(["/usr/bin/pbcopy"], input=payload(blocks[index], kind), text=True, check=True)


def capture_text(args):
    if args.input:
        return args.input.read_text(encoding="utf-8")
    if not args.session or not args.block:
        raise ValueError("--session and --block are required unless --input is used")
    if not shutil.which("rex"):
        raise FileNotFoundError("rex CLI is required to capture a live pane")
    return subprocess.run(
        ["rex", "capture", "-s", args.session, "-b", args.block, "--unwrap"],
        text=True, stdout=subprocess.PIPE, check=True,
    ).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["browse", "edit", "preview"])
    parser.add_argument("--session", help="Rex session containing the source pane")
    parser.add_argument("--block", help="Rex pane to capture")
    parser.add_argument("--input", type=Path, help="Read a saved text capture instead of querying Rex")
    parser.add_argument("--prompt", default=r"^CMD>\s?", help="Regex that identifies a command line")
    parser.add_argument("--prompt-lines", type=int, default=3,
                        help="Prompt lines to remove before the next command (default: 3)")
    args = parser.parse_args()
    if args.prompt_lines < 1:
        parser.error("--prompt-lines must be at least 1")
    text = capture_text(args)
    if args.mode == "preview":
        print(json.dumps(parse_blocks(text, args.prompt, args.prompt_lines), indent=2))
        return
    with tempfile.TemporaryDirectory(prefix="rex-scrollback-") as directory:
        folder = Path(directory)
        if args.mode == "edit":
            capture = folder / "scrollback.txt"
            capture.write_text(text, encoding="utf-8")
            subprocess.run(editor_command(capture), check=True)
            return
        blocks = parse_blocks(text, args.prompt, args.prompt_lines)
        if not blocks:
            print("No command blocks found. Check the CMD> marker, --prompt, and --prompt-lines.")
            if not args.input and sys.stdin.isatty():
                try:
                    input("Press Enter to close this popup.")
                except (EOFError, KeyboardInterrupt):
                    pass
            return
        run_picker(blocks, folder)


if __name__ == "__main__":
    try:
        main()
    except (subprocess.CalledProcessError, OSError, ValueError, re.error) as error:
        print(f"Rex Scrollback Tool: {error}", file=sys.stderr)
        sys.exit(1)
