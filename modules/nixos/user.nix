{ config, lib, ... }:
{
  options.salamah.user.name = lib.mkOption {
    type = lib.types.str;
    default = "salamah";
    description = "Name of the normal user.";
  };

  # No password: VM only. The real PC sets one in M3.
  config.users.users.${config.salamah.user.name} = {
    isNormalUser = true;
    uid = 1000;
    extraGroups = [
      "video"
      "input"
      "wheel"
    ];
  };
}
