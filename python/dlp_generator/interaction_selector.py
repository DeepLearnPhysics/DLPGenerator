import hashlib
import math
import time


SPECIAL_KEYS = {"SEED", "Debug", "InteractionSelection"}


def _derived_seed(seed, name):
    payload = f"DLPGenerator-interaction-stream-v1:{seed}:{name}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big") % 2147000000


class WeightedInteractionSelector:
    """Choose one interaction block per call from reproducible weighted draws."""

    def __init__(self, cfg, weights, generator_factory):
        configured_seed = cfg.get("SEED", -1)
        self._seed = (
            configured_seed
            if configured_seed >= 0
            else time.time_ns() % 2147000000
        )
        self._debug = cfg.get("Debug", False)
        self._weights = dict(weights)
        self._generators = {}
        for name in self._weights:
            block = cfg[name]
            if block.get("NumEvent") != [1, 1]:
                raise ValueError(
                    f"InteractionSelection requires NumEvent: [1, 1] for {name}"
                )
            child_cfg = {
                "SEED": _derived_seed(self._seed, name),
                "Debug": self._debug,
                name: block,
            }
            self._generators[name] = generator_factory(child_cfg)
        self._call = 0
        self._last_generator = next(iter(self._generators.values()))

    def _next_name(self):
        payload = f"DLPGenerator-interaction-draw-v1:{self._seed}:{self._call}".encode()
        draw = int.from_bytes(hashlib.sha256(payload).digest(), "big") / (1 << 256)
        self._call += 1
        threshold = draw * sum(self._weights.values())
        for name, weight in self._weights.items():
            if threshold < weight:
                return name
            threshold -= weight
        return next(reversed(self._weights))

    def Generate(self):
        name = self._next_name()
        if self._debug:
            print(f"[ParticleBomb] Selected interaction {name}")
        self._last_generator = self._generators[name]
        return self._last_generator.Generate()

    def Flatten(self, particles):
        return self._last_generator.Flatten(particles)

    def PrintHierarchy(self, particles):
        return self._last_generator.PrintHierarchy(particles)

    def Configured(self):
        return all(generator.Configured() for generator in self._generators.values())

    def Seed(self, seed=None):
        if seed is None:
            return self._seed
        self._seed = seed if seed >= 0 else time.time_ns() % 2147000000
        for name, generator in self._generators.items():
            generator.Seed(_derived_seed(self._seed, name))
        self._call = 0


def create_interaction_selector(cfg, generator_factory):
    selection = cfg["InteractionSelection"]
    if not isinstance(selection, dict):
        raise ValueError("InteractionSelection must be a mapping")
    if selection.get("Mode") != "weighted_random":
        raise ValueError("InteractionSelection Mode must be weighted_random")
    blocks = [key for key in cfg if key not in SPECIAL_KEYS]
    if not blocks:
        raise ValueError("InteractionSelection requires interaction blocks")
    weights = {name: cfg[name].get("SelectionWeight") for name in blocks}
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
        for value in weights.values()
    ):
        raise ValueError(
            "every selected interaction block requires a finite, positive "
            "SelectionWeight"
        )
    return WeightedInteractionSelector(cfg, weights, generator_factory)
