{
  xdg.configFile."hypr/hyprland.lua".text = ''
    hl.config({
      animations = { enabled = false },
      cursor = { no_hardware_cursors = true },
    })

    hl.on("hyprland.start", function()
      hl.exec_cmd("qs -p ~/.config/quickshell/salamah")
    end)
  '';
  xdg.configFile."quickshell/salamah".source = ../../shell;
  home.stateVersion = "26.11";
}
