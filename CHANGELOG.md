# Changelog

All notable changes to this project will be documented in this file.

## v1.1.1 - 2026-07-13

Patch release for HEPEVT-like event block compatibility.

### Fixed
* add per-event particle-count headers to default HEPEVT-like CLI output
* document that one `Generate()` call maps to one HEPEVT-like event block

## v1.1.0 - 2026-07-13

Minor release for corrected angular generation.

### Changed
* sample particle directions uniformly in solid angle by drawing `cos(theta)` uniformly within the configured theta bounds
* update the `theta_range` documentation comment to make the angular sampling behavior explicit

## v1.0.1 - 2026-07-06

Patch release for ion PDG code generation.

### Fixed
* avoid segmentation faults when ROOT does not have an ion PDG entry in `TDatabasePDG`
* approximate valid ion masses from proton and neutron counts so generation can continue
* warn once per ion PDG when the fallback mass ignores nuclear binding energy
* reject empty or unsupported PDG lists during generator configuration instead of failing during generation

## v1.0.0 - 2026-07-02

Initial tagged release of DLPGenerator as a standalone ROOT-based particle generator package.

### Added
* `dlpgen` command-line interface for running YAML configurations directly
* HEPEVT-like text output mode for generated particle rows
* CSV output mode with stable per-call, per-interaction, and per-particle identifiers
* `bomb-macro` output mode for generating `edep-sim` bomb macros from the same YAML configuration
* Docker image build based on `rootproject/root:6.32.02-ubuntu22.04`
* GitHub Actions workflow to publish container images to `ghcr.io/deeplearnphysics/dlpgen` when a GitHub Release is published

### Changed
* standardized the public-facing command and container image name to `dlpgen`
* rewrote the top-level README to describe DLPGenerator rather than legacy LiteFMWK content
* documented Docker usage, native ROOT-based builds, CLI usage, and Python usage
* made the Python package imports lazy so non-generator output modes do not require loading ROOT at import time

### Notes
* Native builds still require a working ROOT 6 environment with `root-config`, `rootcling`, and PyROOT
* Published containers target `linux/amd64` to match the upstream ROOT base image
