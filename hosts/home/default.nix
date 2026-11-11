{
  imports = [
    ../../modules/nixos/user.nix
    ../../modules/nixos/desktop.nix
  ];
  networking.hostName = "home";
  system.stateVersion = "26.11";
}
