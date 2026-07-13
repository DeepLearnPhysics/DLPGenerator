# DLPGenerator

[![Publish Docker Image](https://github.com/DeepLearnPhysics/DLPGenerator/actions/workflows/publish-docker.yml/badge.svg)](https://github.com/DeepLearnPhysics/DLPGenerator/actions/workflows/publish-docker.yml)
[![GHCR Image](https://img.shields.io/badge/ghcr.io-deeplearnphysics%2Fdlpgen-blue)](https://github.com/DeepLearnPhysics/DLPGenerator/pkgs/container/dlpgen)

`DLPGenerator` is a configurable particle event generator used to produce synthetic interaction topologies for simulation and downstream ML workflows. The core generator is the C++ class `DLPGenerator::ParticleBomb`, built with ROOT dictionary support so it can be driven from PyROOT and simple Python helpers.

At a high level, the package lets you:
* describe one or more interaction templates in YAML
* sample particle content, positions, times, and kinetic energies from configurable ranges
* run the generator from Python or the `dlpgen` CLI
* export generated events as HEPEVT-like text, CSV with identifiers, or an `edep-sim` bomb macro

## What the generator produces
One call to `Generate()` returns one batch of generated interactions. A configuration can ask for a variable number of interactions per call via `NumEvent`, and each interaction can contain a variable number of particles selected from configured species and multiplicity ranges.

The generator can then flatten that nested structure into the 15-column HEPEVT-like row format commonly used to hand particles to Geant-based simulation stages.

## Requirements
To build and run the native generator outside Docker, you need:
* ROOT 6 with `root-config`, `rootcling`, and PyROOT available in your environment
* a C++ compiler (`clang++` or `g++`)
* Python 3
* `PyYAML`
* `NumPy` for the optional include-path helper used by `setup.sh`

## Build in an environment that already has ROOT
If you already have a working ROOT installation, the native build is short:

```
source /path/to/your/root/bin/thisroot.sh
source setup.sh
make
```

What this does:
* `source setup.sh` checks that `rootcling` is on `PATH`
* it exports `DLPGENERATOR_DIR`, `DLPGENERATOR_BINDIR`, `DLPGENERATOR_LIBDIR`, `PYTHONPATH`, and the shared-library search path
* `make` builds the `ParticleBomb` package and ROOT dictionary into `build/`

Useful follow-up commands:
```
dlpgen --help
make clean
```

If `PyYAML` is missing, install it in the Python you plan to use for the CLI or Python bindings. If `rootcling` is missing, fix the ROOT environment first and then re-run `source setup.sh`.

## Quick Python check
After building, you can verify that the package imports and generates events:

```
python3 - <<'PY'
import yaml
from dlp_generator import create_generator, EXAMPLE_CONFIG

cfg = yaml.load(EXAMPLE_CONFIG, Loader=yaml.Loader)
gen = create_generator(cfg)
result = gen.Generate()

print(f"Generated {len(result)} interaction block(s)")
print(f"Flattened particle count: {len(gen.Flatten(result))}")
PY
```

## Running with Docker
The repository includes a `Dockerfile` based on the official `rootproject/root` image so you can build and run the generator without installing ROOT directly on the host.

Pull a published release image from GitHub Container Registry:
```
docker pull ghcr.io/deeplearnphysics/dlpgen:latest
```

Build the image from the repository root:
```
docker build -t dlpgen .
```

If you are building on Apple Silicon and want to match the upstream ROOT image architecture explicitly:
```
docker build --platform=linux/amd64 -t dlpgen .
```

Start an interactive container with the repository mounted at runtime:
```
docker run --rm -it \
  -v "$PWD":/workspace/DLPGenerator \
  -w /workspace/DLPGenerator \
  dlpgen /bin/bash
```

Inside the container, source the setup script before using the Python module or the compiled library interactively:
```
source setup.sh
```

Published images are pushed to GitHub Container Registry as `ghcr.io/deeplearnphysics/dlpgen:<tag>` when a GitHub Release is published.
If the GitHub release tag is prefixed with `v` (for example `v1.0.0`), the published container tag is the stripped semver form (`1.0.0`) so pulls match the convention used by other DeepLearnPhysics images.

## CLI usage
After `source setup.sh`, the repository exposes a `dlpgen` command from `bin/`. In the Docker image, the command is on `PATH` by default. The Python import path remains `dlp_generator`.

Run a config and call the generator a fixed number of times, dumping the resulting rows in the default HEPEVT-like text format. Each `Generate()` call is emitted as one event block: a particle-count header followed by 15-column particle rows.
```
dlpgen my_config.yaml 10
```

Write the dumped output to a file instead of stdout:
```
dlpgen my_config.yaml 10 --output events.hepevt
```

Emit CSV with a header and explicit identifiers for generator call, interaction, and particle row:
```
dlpgen my_config.yaml 10 --format csv --output events.csv
```

Emit an `edep-sim` bomb macro modeled on the production setup:
```
dlpgen my_config.yaml 10 --format bomb-macro --output g4.mac
```

Override the config seed or enable debug output:
```
dlpgen my_config.yaml 10 --seed 123 --debug
```

The positional count is the number of `Generate()` calls, not the number of interactions. If the config has `NumEvent: [1, 10]`, one call can emit between 1 and 10 interactions. In the default HEPEVT-like output, all rows from one call are grouped under one particle-count header, and calls are separated by a blank line.

In `bomb-macro` mode, the positional count is emitted as `/run/beamOn <count>`, which is the production-style mapping of one bomb generator invocation per Geant event. The production workflow uses one macro per job, not one macro per event.

In CSV mode, each row includes a header plus these identifiers:
* `call_id` = zero-based `Generate()` call index
* `interaction_id` = zero-based interaction index within that call
* `particle_id` = zero-based particle row index within the flattened call
* `particle_in_interaction` = zero-based particle row index within that interaction

## Python usage
The helper `create_generator` parses a Python `dict` with the expected YAML structure and returns a configured `DLPGenerator.ParticleBomb` instance.

```
import yaml
from dlp_generator import create_generator, EXAMPLE_CONFIG

cfg = yaml.load(EXAMPLE_CONFIG, Loader=yaml.Loader)
cfg['Debug'] = True

gen = create_generator(cfg)
batch = gen.Generate()
hepevt_rows = gen.Flatten(batch)
gen.PrintHierarchy(hepevt_rows)
```

## Configuration model
Each top-level YAML key other than `SEED` and `Debug` is treated as an interaction block. An interaction block configures:
* `NumEvent`: number of interactions to generate per `Generate()` call
* `NumParticle`: total particle multiplicity range for an interaction
* `XRange`, `YRange`, `ZRange`, `TRange`: uniform position and time ranges
* `AddParent`: whether to add a synthetic parent/root particle
* `Particles`: one or more particle templates

Each particle template configures:
* `PDG`: allowed PDG codes to sample from
* `NumRange`: multiplicity range for that particle template
* `KERange`: kinetic-energy range
* `UseMom`: interpret the energy range as momentum instead of kinetic energy
* `Weight`: relative sampling weight

See the documentation notebooks in `book/Introduction.md` and `book/Configuration.md` for worked examples.
 
