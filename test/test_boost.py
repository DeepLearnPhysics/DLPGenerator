import copy
import math
import unittest

from ROOT import DLPGenerator as G
from dlp_generator.config_parser import create_generator
from test_particle_bomb import interaction, particle


def boost_config(boost=None, events=1, kinetic=0.0, parent=False):
    block = {
        "NumEvent": [events, events],
        "NumParticle": [2, 2],
        "XRange": [1.0, 10.0],
        "YRange": [2.0, 20.0],
        "ZRange": [3.0, 30.0],
        "TRange": [4.0, 40.0],
        "AddParent": parent,
        "Particles": [
            {"PDG": [pdg], "NumRange": [1, 1], "KERange": [kinetic, kinetic], "Weight": 1}
            for pdg in (13, 2212)
        ],
    }
    if boost is not None:
        block["Boost"] = boost
    return {"SEED": 12345, "Bomb": block}


def generate(cfg):
    generator = create_generator(cfg)
    return [tuple(row) for row in generator.Flatten(generator.Generate())]


class BoostTest(unittest.TestCase):
    def test_zero_boost_preserves_all_seeded_output(self):
        baseline = boost_config(events=10, kinetic=1.0, parent=True)
        zero = copy.deepcopy(baseline)
        zero["Bomb"]["Boost"] = {"BetaGammaRange": [0, 0], "Direction": [1, 2, 3]}
        self.assertEqual(generate(baseline), generate(zero))

    def test_known_boost_of_rest_particles_and_parent(self):
        rows = generate(boost_config(
            {"BetaGammaRange": [2, 2], "Direction": [0, 0, 7]}, parent=True
        ))
        parent, *children = rows
        for row in children:
            self.assertAlmostEqual(row[6], 0.)
            self.assertAlmostEqual(row[7], 0.)
            self.assertAlmostEqual(row[8], 2 * row[10])
            self.assertAlmostEqual(row[9], math.sqrt(5) * row[10])
        for column in (6, 7, 8, 9):
            self.assertAlmostEqual(parent[column], sum(row[column] for row in children))
        self.assertEqual(parent[4:6], (1., 2.))
        self.assertEqual(children[0][2:4], (0., 0.))

    def test_moving_particles_obey_common_lorentz_transform(self):
        cfg = boost_config(kinetic=1.0, parent=True)
        cfg["Bomb"]["ShootInward"] = 1
        cfg["Bomb"]["ShootInwardStrict"] = True
        before = generate(cfg)
        cfg["Bomb"]["Boost"] = {"BetaGammaRange": [2, 2], "Direction": [1, -2, 3]}
        after = generate(cfg)
        direction = [v / math.sqrt(14) for v in (1, -2, 3)]
        gamma = math.sqrt(5)
        for old, new in zip(before, after):
            dot = sum(old[6 + i] * direction[i] for i in range(3))
            self.assertAlmostEqual(new[9], gamma * old[9] + 2 * dot)
            for i in range(3):
                expected = old[6 + i] + ((gamma - 1) * dot + 2 * old[9]) * direction[i]
                self.assertAlmostEqual(new[6 + i], expected)
            self.assertEqual(old[:6], new[:6])
            self.assertEqual(old[10:], new[10:])  # masses, vertex, time unchanged
            old_mass2 = old[9] ** 2 - sum(v * v for v in old[6:9])
            new_mass2 = new[9] ** 2 - sum(v * v for v in new[6:9])
            self.assertAlmostEqual(old_mass2, new_mass2)

    def test_photons_stay_massless(self):
        cfg = boost_config({"BetaGammaRange": [3, 3], "Direction": [-1, 0, 0]}, kinetic=1)
        cfg["Bomb"]["Particles"][0]["PDG"] = [22]
        for row in generate(cfg):
            self.assertAlmostEqual(row[9] ** 2 - sum(v*v for v in row[6:9]), row[10] ** 2)

    def test_isotropic_directions_and_uniform_magnitude_per_interaction(self):
        cfg = boost_config({"BetaGammaRange": [1, 3]}, events=3000)
        rows = generate(cfg)
        self.assertEqual(rows, generate(cfg))
        vectors = []
        magnitudes = []
        for first, second in zip(rows[::2], rows[1::2]):
            vector = [first[6+i] / first[10] for i in range(3)]
            for i in range(3):
                self.assertAlmostEqual(vector[i], second[6+i] / second[10])
            magnitude = math.sqrt(sum(v*v for v in vector))
            self.assertGreaterEqual(magnitude, 1)
            self.assertLessEqual(magnitude, 3)
            magnitudes.append(magnitude)
            vectors.append([v / magnitude for v in vector])
        self.assertAlmostEqual(sum(magnitudes) / len(magnitudes), 2, delta=0.04)
        for axis in range(3):
            self.assertAlmostEqual(sum(v[axis] for v in vectors) / len(vectors), 0, delta=0.04)
            self.assertAlmostEqual(sum(v[axis]**2 for v in vectors) / len(vectors), 1/3, delta=0.04)

    def test_angular_window_samples_uniform_cos_theta(self):
        cfg = boost_config({
            "BetaGammaRange": [1, 1], "PhiRange": [0.3, 0.8], "ThetaRange": [0.4, 1.2],
        }, events=2000)
        cosines, phis = [], []
        for row in generate(cfg)[::2]:
            magnitude = math.sqrt(sum(v*v for v in row[6:9]))
            cosine = row[8] / magnitude
            phi = math.atan2(row[7], row[6])
            self.assertTrue(math.cos(1.2) <= cosine <= math.cos(0.4))
            self.assertTrue(0.3 <= phi <= 0.8)
            cosines.append(cosine)
            phis.append(phi)
        self.assertAlmostEqual(sum(cosines)/len(cosines), (math.cos(1.2)+math.cos(0.4))/2, delta=0.015)
        self.assertAlmostEqual(sum(phis)/len(phis), 0.55, delta=0.015)

    def test_fixed_angles_match_direction_vector(self):
        first = boost_config({"BetaGammaRange": [1, 1], "Direction": [0, 0, -1]})
        second = boost_config({
            "BetaGammaRange": [1, 1], "PhiRange": [0, 0], "ThetaRange": [math.pi, math.pi],
        })
        self.assertEqual(generate(first), generate(second))

    def test_invalid_yaml_boost_is_rejected(self):
        invalid = [
            None, True, {}, {"BetaGammaRange": [-1, 1]}, {"BetaGammaRange": [2, 1]},
            {"BetaGammaRange": [0, float("inf")]}, {"BetaGammaRange": [0, float("nan")]},
            {"BetaGammaRange": [True, 1]}, {"BetaGammaRange": [1]},
            {"BetaGammaRange": [1, 1], "Direction": [0, 0, 0]},
            {"BetaGammaRange": [1, 1], "Direction": [1, 0]},
            {"BetaGammaRange": [1, 1], "Direction": [1, 0, float("nan")]},
            {"BetaGammaRange": [1, 1], "Direction": [1, 0, 0], "ThetaRange": [0, 1]},
            {"BetaGammaRange": [1, 1], "PhiRange": [0, 7]},
            {"BetaGammaRange": [1, 1], "ThetaRange": [0, 4]},
            {"BetaGammaRange": [1, 1], "Typo": 1},
        ]
        for boost in invalid:
            with self.subTest(boost=boost):
                cfg = boost_config()
                cfg["Bomb"]["Boost"] = boost
                with self.assertRaises(ValueError):
                    create_generator(cfg)

    def test_cpp_validation(self):
        for name, values, code in (
            ("boost_betagamma_range", (-1, 1), 18),
            ("boost_betagamma_range", (0, float("nan")), 18),
            ("boost_betagamma_range", (2, 1), 18),
            ("boost_phi_range", (0, 7), 19),
            ("boost_theta_range", (0, float("inf")), 20),
        ):
            with self.subTest(name=name, values=values):
                cfg = interaction((1, 1), [particle([13], (1, 1))])
                bounds = getattr(cfg, name)
                bounds[0], bounds[1] = values
                generator = G.ParticleBomb(1)
                self.assertEqual(generator.Add(cfg), code)
                self.assertFalse(generator.Configured())


if __name__ == "__main__":
    unittest.main()
