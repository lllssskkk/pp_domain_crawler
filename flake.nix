{
  description = "Reproducible JS-crawler with Selenium-Wire (fixed)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true; # remove if you don't need google-chrome
        };

      
        # ── 1. optional package overrides ──────────────────────────────────
        pyOverrides = final: prev: {
          # Example – only keep if nixpkgs still ships 5.0.x:
          selenium-wire = prev.selenium-wire.overridePythonAttrs (old: rec {
            version = "5.1.0";
            src = pkgs.fetchPypi {
              pname = "selenium-wire";
              inherit version;
              sha256 = "sha256-sc1OrkTZlZOBq+O7GGRyUg0GPGWOJ5+YVV3vPU5t0ps=";
            };

            doCheck = false;

            # remove the flag that aborts evaluation
            meta = {
              description = "Capture HTTP(S) traffic from Selenium";
              homepage = "https://github.com/wkeeling/selenium-wire";
              broken = false; # ← removes the break-flag cleanly
            };
          });

          blinker = prev.blinker.overridePythonAttrs (old: rec {
            version = "1.7.0";
            src = pkgs.fetchPypi {
              pname = "blinker";
              inherit version;
              sha256 = "sha256-5oIP9vpOTR2OJ0fCKDdJw/VH5P7hErmFVc3NrjKZYYI=";
            };
          });
        };

        # Here is the *fixed* bit ↓↓↓
        python = pkgs.python312.override { packageOverrides = pyOverrides; };
        pythonEnv = python.withPackages (
          ps: with ps; [
            attrs
            blinker
            brotli
            certifi
            cffi
            cryptography
            editorconfig
            h11
            h2
            hpack
            hyperframe
            idna
            jsbeautifier
            kaitaistruct
            outcome
            pyasn1
            pycparser
            pyparsing
            selenium
            selenium-wire
            setuptools
            six
            sniffio
            sortedcontainers
            tqdm
            trio
            trio-websocket
            typing-extensions
            urllib3
            websocket-client
            wsproto
            zstandard
            pyopenssl
            pysocks
          ]
        );

        # ── 2. browser & driver ────────────────────────────────────────────
        browserPkgs = [
          pkgs.google-chrome
          pkgs.chromedriver
        ];
        # If you prefer FOSS chromium:
        # browserPkgs = [ pkgs.chromium pkgs.chromedriver ];

        # ── 3. dev-shell ───────────────────────────────────────────────────
        devShell = pkgs.mkShell {
          packages = [ pythonEnv ] ++ browserPkgs ++ [ pkgs.ruff ];
          shellHook = ''
            export PATH=${pkgs.chromedriver}/bin:$PATH
          '';
        };

        # ── 4. wrapper for nix run / nix build ────────────────────────────
        runScript = pkgs.writeShellApplication {
          name = "crawler";
          runtimeInputs = [ pythonEnv ] ++ browserPkgs ;
          text = ''
            export PATH=${pkgs.chromedriver}/bin:$PATH
            exec ${pythonEnv.interpreter} ${self}/crawler.py "$@"
          '';
        };
      in
      {
        devShells.default = devShell;
        packages.default = runScript;
        apps.default = flake-utils.lib.mkApp { drv = runScript; };
      }
    );
}
