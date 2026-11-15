-- Add these actions to the Rex configuration.
local function executable()
  local configured = os.getenv("REX_SCROLLBACK_BIN")
  if configured and configured ~= "" then return configured end

  local tool_bin = os.getenv("UV_TOOL_BIN_DIR")
  if not tool_bin or tool_bin == "" then
    local home = os.getenv("HOME")
    if home and home ~= "" then tool_bin = home .. "/.local/bin" end
  end
  if tool_bin then return tool_bin .. "/rex-scrollback" end
  return "rex-scrollback"
end

local function open_history(ctx, mode)
  if not ctx.session_id or not ctx.block_id then
    error("Select a terminal pane first", 0)
  end
  local result, err = rex.session.new_layer{
    session_id = ctx.session_id,
    bounds = { 0.08, 0.08, 0.84, 0.84 },
    focus = true,
    layout = rex.layout.block{
      flavor = "com.superlogical.terminal.shell",
      options = {
        command = { executable(), mode, "--session", ctx.session_id, "--block", ctx.block_id },
      },
    },
  }
  if not result then error(err or "Could not open history popup", 0) end
end

rex.action{
  name = "browse_command_history",
  title = "Browse Command History",
  description = "Search this pane's captured commands and copy command, output, or both",
  run = function(ctx) open_history(ctx, "browse") end,
}
rex.action{
  name = "edit_scrollback",
  title = "Edit Scrollback",
  description = "Open this pane's captured scrollback in VISUAL, EDITOR, or nvim",
  run = function(ctx) open_history(ctx, "edit") end,
}
