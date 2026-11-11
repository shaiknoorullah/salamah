{
  name = "desktop-e2e";

  enableOCR = true;

  nodes.machine.imports = [
    ../../hosts/home
    ../vm
  ];

  testScript = ''
    machine.wait_for_unit("multi-user.target")
    machine.wait_until_succeeds("ls /run/user/1000/hypr/*/.socket.sock", timeout=180)
    hypr = "su - salamah -c 'XDG_RUNTIME_DIR=/run/user/1000 HYPRLAND_INSTANCE_SIGNATURE=$(ls /run/user/1000/hypr) hyprctl {}'"
    machine.wait_until_succeeds(hypr.format("-j layers") + " | grep -q quickshell", timeout=180)
    assert machine.succeed(hypr.format("configerrors")).strip() in ("", "[]")

    # J1: boot to bar
    machine.wait_for_text("salamah")
    machine.screenshot("j1-bar")
  '';
}
