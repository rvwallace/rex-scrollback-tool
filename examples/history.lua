-- Add these actions to the Rex configuration.
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
        command = { "rex-scrollback", mode, "--session", ctx.session_id, "--block", ctx.block_id },
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
