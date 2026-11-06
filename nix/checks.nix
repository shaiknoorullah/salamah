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

  docs =
    pkgs.runCommand "salamah-docs"
      {
        nativeBuildInputs = [
          pkgs.python3
          pkgs.rumdl
          pkgs.vale
          pkgs.lychee
          pkgs.cacert
        ];
      }
      ''
        export HOME=$TMPDIR
        export SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt
        cp -r ${self} src
        chmod -R u+w src
        cd src
        python3 -m tools.docs check
        rumdl check --config .config/rumdl.toml .
        vale --config .config/vale.ini docs $(ls README.md AGENTS.md 2>/dev/null)
        lychee --offline --include-fragments --config .config/lychee.toml 'docs/**/*.md' README.md
        touch $out
      '';
}
