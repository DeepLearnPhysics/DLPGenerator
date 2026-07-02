import argparse
import csv
import os
import sys

import yaml


HEPEVT_COLUMNS = [
    "status_code",
    "pdg_code",
    "parent0",
    "parent1",
    "child_first",
    "child_last",
    "px",
    "py",
    "pz",
    "energy",
    "mass",
    "x",
    "y",
    "z",
    "t",
]

CSV_COLUMNS = [
    "call_id",
    "interaction_id",
    "particle_id",
    "particle_in_interaction",
    *HEPEVT_COLUMNS,
]


def _format_value(value):
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def _load_config(path):
    with open(path, "r", encoding="utf-8") as config_file:
        return yaml.load(config_file, Loader=yaml.Loader)


def _write_hepevt_call(output_stream, flattened_call):
    for particle in flattened_call:
        output_stream.write(" ".join(_format_value(value) for value in particle))
        output_stream.write("\n")


def _write_csv_call(writer, batch, generator, call_id):
    particle_id = 0
    for interaction_id, interaction in enumerate(batch):
        flattened_interaction = generator.Flatten([interaction])
        for particle_in_interaction, particle in enumerate(flattened_interaction):
            row = {
                "call_id": call_id,
                "interaction_id": interaction_id,
                "particle_id": particle_id,
                "particle_in_interaction": particle_in_interaction,
            }
            row.update(dict(zip(HEPEVT_COLUMNS, particle)))
            writer.writerow(row)
            particle_id += 1


def _write_bomb_macro(output_stream, config_path, num_calls):
    output_stream.write("/edep/random/timeRandomSeed\n")
    output_stream.write(f"/generator/kinematics/bomb/config {config_path}\n")
    output_stream.write("/generator/kinematics/bomb/verbose 0\n")
    output_stream.write("/generator/kinematics/set bomb\n\n")
    output_stream.write("/generator/count/fixed/number 1\n")
    output_stream.write("/generator/count/set fixed\n")
    output_stream.write("/generator/add\n\n")
    output_stream.write(f"/run/beamOn {num_calls}\n")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run DLPGenerator from a YAML config and dump HEPEVT-like output."
    )
    parser.add_argument("config", help="Path to a YAML configuration file")
    parser.add_argument(
        "num_calls",
        type=int,
        help="Number of times to call generator.Generate()",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write output to a file instead of stdout",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Override the random seed from the config",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable generator debug output",
    )
    parser.add_argument(
        "--format",
        choices=("hepevt", "csv", "bomb-macro"),
        default="hepevt",
        help="Output format. 'hepevt' preserves the original 15-column dump, 'csv' adds row identifiers and a header, and 'bomb-macro' emits an edep-sim macro modeled on production bomb usage.",
    )

    args = parser.parse_args(argv)

    if args.num_calls <= 0:
        parser.error("num_calls must be positive")

    if args.format == "bomb-macro":
        if args.seed is not None:
            parser.error("--seed is not supported with --format bomb-macro")
        if args.debug:
            parser.error("--debug is not supported with --format bomb-macro")

        output_stream = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout
        try:
            _write_bomb_macro(output_stream, args.config, args.num_calls)
        finally:
            if args.output:
                output_stream.close()
        return 0

    config = _load_config(args.config)
    if args.seed is not None:
        config["SEED"] = args.seed
    if args.debug:
        config["Debug"] = True

    from .config_parser import create_generator

    generator = create_generator(config)

    output_stream = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout
    try:
        csv_writer = None
        if args.format == "csv":
            csv_writer = csv.DictWriter(output_stream, fieldnames=CSV_COLUMNS)
            csv_writer.writeheader()

        for call_id in range(args.num_calls):
            batch = generator.Generate()
            if not batch:
                raise RuntimeError("Generator returned no events")

            if args.format == "csv":
                _write_csv_call(csv_writer, batch, generator, call_id)
            else:
                flattened_call = generator.Flatten(batch)
                _write_hepevt_call(output_stream, flattened_call)
                if call_id + 1 < args.num_calls:
                    output_stream.write("\n")
    finally:
        if args.output:
            output_stream.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())