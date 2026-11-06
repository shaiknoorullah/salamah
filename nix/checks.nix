{
  pkgs,
  self,
  formatting,
}:
{
  inherit formatting;

  unit =
    pkgs.runCommand "salamah-unit"
      {
        nativeBuildInputs = [
          (pkgs.python3.withPackages (ps: [
            ps.pytest
            ps.pillow
          ]))
          pkgs.git
        ];
      }
      ''
        export HOME=$TMPDIR
        export GIT_CONFIG_GLOBAL=/dev/null
        cp -r ${self} src
        chmod -R u+w src
        cd src
        python3 -m pytest -c .config/pytest.ini tools
        touch $out
      '';
}
