{
  config,
  pkgs,
  inputs,
  ...
}:
{
  imports = [ inputs.home-manager.nixosModules.home-manager ];
  programs.hyprland.enable = true;
  services.greetd = {
    enable = true;
    settings.initial_session = {
      command = "start-hyprland";
      user = config.salamah.user.name;
    };
    settings.default_session = {
      command = "${pkgs.greetd}/bin/agreety --cmd start-hyprland";
      user = "greeter";
    };
  };
  environment.systemPackages = [ pkgs.quickshell ];
  fonts.packages = [ pkgs.jetbrains-mono ];
  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;
    backupFileExtension = "pre-salamah";
    users.${config.salamah.user.name} = import ../home/desktop.nix;
  };
}
