import math
import unittest

from ROOT import DLPGenerator as G
from dlp_generator.config_parser import create_generator, parse_shoot_inward


def particle(pdg, multiplicity, weight=1.0, kerange=(0.0, 0.0)):
    param = G.GenParamParticle()
    for code in pdg:
        param.pdg.push_back(code)
    param.multi[0], param.multi[1] = multiplicity
    param.kerange[0], param.kerange[1] = kerange
    param.weight = weight
    return param


def interaction(num_particle, particles, num_event=(1, 1)):
    param = G.GenParamInteraction()
    param.num_event[0], param.num_event[1] = num_event
    param.num_particle[0], param.num_particle[1] = num_particle
    param.xrange[0], param.xrange[1] = (0.0, 0.0)
    param.yrange[0], param.yrange[1] = (0.0, 0.0)
    param.zrange[0], param.zrange[1] = (0.0, 0.0)
    param.trange[0], param.trange[1] = (0.0, 0.0)
    for item in particles:
        param.part_param_v.push_back(item)
    return param


class ParticleMultiplicityTest(unittest.TestCase):
    def test_required_electron_is_always_generated(self):
        generator = G.ParticleBomb(12345)
        config = interaction(
            (1, 6),
            [particle([11], (1, 1)), particle([13], (0, 5))],
            num_event=(500, 500),
        )

        self.assertEqual(generator.Add(config), 0)
        generated = generator.Generate()

        self.assertEqual(len(generated), 500)
        for event in generated:
            pdgs = [item.pdg_code for item in event]
            self.assertEqual(pdgs.count(11), 1)
            self.assertGreaterEqual(len(event), 1)
            self.assertLessEqual(len(event), 6)

    def test_required_particle_is_generated_even_with_zero_weight(self):
        generator = G.ParticleBomb(7)
        config = interaction(
            (2, 2),
            [particle([11], (1, 1), weight=0.0), particle([13], (0, 1))],
        )

        self.assertEqual(generator.Add(config), 0)
        pdgs = [item.pdg_code for item in generator.Generate()[0]]
        self.assertEqual(pdgs.count(11), 1)
        self.assertEqual(pdgs.count(13), 1)

    def test_rejects_minima_that_do_not_fit_all_event_sizes(self):
        generator = G.ParticleBomb(1)
        config = interaction(
            (1, 6),
            [particle([11], (1, 1)), particle([13], (1, 5))],
        )

        self.assertEqual(generator.Add(config), 15)
        self.assertFalse(generator.Configured())

    def test_rejects_insufficient_weighted_capacity(self):
        generator = G.ParticleBomb(1)
        config = interaction(
            (1, 6),
            [particle([11], (1, 1)), particle([13], (0, 4))],
        )

        self.assertEqual(generator.Add(config), 16)
        self.assertFalse(generator.Configured())

    def test_zero_weight_capacity_does_not_count_as_selectable(self):
        generator = G.ParticleBomb(1)
        config = interaction(
            (1, 2),
            [particle([11], (1, 1)), particle([13], (0, 1), weight=0.0)],
        )

        self.assertEqual(generator.Add(config), 16)


INWARD_LO = (0.0, 0.0, 0.0)
INWARD_HI = (2000.0, 1000.0, 5000.0)


def inward_config(shoot_inward, seed=12345, num_event=4000):
    block = {
        "NumEvent": [num_event, num_event],
        "NumParticle": [1, 1],
        "XRange": [INWARD_LO[0], INWARD_HI[0]],
        "YRange": [INWARD_LO[1], INWARD_HI[1]],
        "ZRange": [INWARD_LO[2], INWARD_HI[2]],
        "TRange": [0.0, 0.0],
        "ShootInward": shoot_inward,
        "Particles": [
            {
                "PDG": [13],
                "NumRange": [1, 1],
                "KERange": [1.0, 1.0],
                "UseMom": False,
                "Weight": 1,
            }
        ],
    }
    return {"SEED": seed, "Bomb": block}


def path_inside_volume(row):
    """Distance the particle travels before leaving the generation volume."""
    # PyROOT exposes std::array without slicing, so index one element at a time
    vertex = [row[11], row[12], row[13]]
    momentum = [row[6], row[7], row[8]]
    magnitude = math.sqrt(sum(value * value for value in momentum))
    best = float("inf")
    for axis in range(3):
        direction = momentum[axis] / magnitude
        if abs(direction) < 1e-15:
            continue
        wall = INWARD_HI[axis] if direction > 0 else INWARD_LO[axis]
        best = min(best, (wall - vertex[axis]) / direction)
    return best


def inward_paths(shoot_inward):
    generator = create_generator(inward_config(shoot_inward))
    return [path_inside_volume(row) for row in generator.Flatten(generator.Generate())]


def near_corner(row):
    """True when the vertex sits in the outer eighth of every axis."""
    for axis in range(3):
        lo, hi = INWARD_LO[axis], INWARD_HI[axis]
        margin = 0.125 * (hi - lo)
        if lo + margin <= row[11 + axis] <= hi - margin:
            return False
    return True


class ShootInwardTest(unittest.TestCase):
    def test_inward_sampling_lengthens_the_path_inside_the_volume(self):
        isotropic = inward_paths(False)
        inward = inward_paths(True)

        self.assertEqual(len(inward), 4000)
        self.assertGreater(
            sum(inward) / len(inward), 1.15 * sum(isotropic) / len(isotropic)
        )

    def test_inward_sampling_wastes_far_fewer_throws(self):
        isotropic = inward_paths(False)
        inward = inward_paths(True)

        wasted = sum(1 for value in inward if value < 200.0) / len(inward)
        baseline = sum(1 for value in isotropic if value < 200.0) / len(isotropic)
        self.assertLess(wasted, 0.6 * baseline)

    def test_corner_vertices_are_the_ones_that_gain(self):
        # A hemisphere cut barely helps a vertex near a corner, because half of the
        # retained directions still leave through the two nearby walls.
        generator = create_generator(inward_config(True, num_event=20000))
        rows = [row for row in generator.Flatten(generator.Generate()) if near_corner(row)]
        self.assertGreater(len(rows), 200)

        wasted = sum(1 for row in rows if path_inside_volume(row) < 200.0) / len(rows)
        self.assertLess(wasted, 0.25)

    def test_power_zero_reproduces_isotropic_sampling(self):
        isotropic = inward_paths(False)
        unbiased = inward_paths(0)

        self.assertAlmostEqual(
            sum(unbiased) / len(unbiased),
            sum(isotropic) / len(isotropic),
            delta=0.08 * sum(isotropic) / len(isotropic),
        )

    def test_the_bias_grows_with_the_power(self):
        means = [
            sum(values) / len(values)
            for values in (
                inward_paths(0),
                inward_paths(1),
                inward_paths(3),
            )
        ]

        self.assertEqual(means, sorted(means))
        self.assertGreater(means[2], 1.5 * means[0])

    def test_zero_extent_volume_stays_isotropic(self):
        # No direction travels any distance, so there is nothing to bias toward.
        generator = G.ParticleBomb(1)
        config = interaction(
            (1, 1), [particle([13], (1, 1), kerange=(1.0, 1.0))], num_event=(2000, 2000)
        )
        config.shoot_inward_power = 1.0

        self.assertEqual(generator.Add(config), 0)
        rows = generator.Flatten(generator.Generate())

        self.assertEqual(len(rows), 2000)
        self.assertGreater(sum(1 for row in rows if row[8] < 0.0), 900)
        self.assertLess(sum(1 for row in rows if row[8] < 0.0), 1100)

    def test_rejects_a_negative_power(self):
        generator = G.ParticleBomb(1)
        config = interaction((1, 1), [particle([13], (1, 1))])
        config.shoot_inward_power = -1.0

        self.assertEqual(generator.Add(config), 17)
        self.assertFalse(generator.Configured())

    def test_booleans_are_shorthand_for_a_strength(self):
        self.assertEqual(parse_shoot_inward(True), 1.0)
        self.assertEqual(parse_shoot_inward(False), 0.0)
        self.assertEqual(parse_shoot_inward(2.5), 2.5)
        self.assertEqual(parse_shoot_inward(0), 0.0)

    def test_true_and_one_configure_the_same_generator(self):
        self.assertEqual(inward_paths(True), inward_paths(1))
        self.assertEqual(inward_paths(False), inward_paths(0))

    def test_rejects_a_shoot_inward_value_that_is_not_a_strength(self):
        for value in ("yes", -1, float("nan")):
            with self.assertRaisesRegex(ValueError, "boolean or a non-negative number"):
                create_generator(inward_config(value))


def selected_config(seed=12345):
    def block(pdg):
        return {
            "SelectionWeight": 1,
            "NumEvent": [1, 1],
            "NumParticle": [1, 1],
            "XRange": [0.0, 0.0],
            "YRange": [0.0, 0.0],
            "ZRange": [0.0, 0.0],
            "TRange": [0.0, 0.0],
            "Particles": [
                {
                    "PDG": [pdg],
                    "NumRange": [1, 1],
                    "KERange": [0.0, 0.0],
                    "UseMom": False,
                    "Weight": 1,
                }
            ],
        }

    return {
        "SEED": seed,
        "InteractionSelection": {
            "Mode": "weighted_random",
        },
        "CC": block(11),
        "NC": block(211),
    }


class InteractionSelectionTest(unittest.TestCase):
    def test_equal_weight_draws_are_reproducible_and_statistically_balanced(self):
        first = create_generator(selected_config())
        second = create_generator(selected_config())
        first_pdgs = [first.Generate()[0][0].pdg_code for _ in range(1000)]
        second_pdgs = [second.Generate()[0][0].pdg_code for _ in range(1000)]

        self.assertEqual(first_pdgs, second_pdgs)
        self.assertGreater(first_pdgs.count(11), 450)
        self.assertLess(first_pdgs.count(11), 550)
        self.assertTrue(
            any(first_pdgs[index] == first_pdgs[index + 1] for index in range(999))
        )

    def test_selected_blocks_must_each_generate_one_interaction(self):
        config = selected_config()
        config["CC"]["NumEvent"] = [1, 2]
        with self.assertRaisesRegex(ValueError, r"NumEvent: \[1, 1\]"):
            create_generator(config)

    def test_every_block_requires_a_selection_weight(self):
        config = selected_config()
        del config["NC"]["SelectionWeight"]
        with self.assertRaisesRegex(ValueError, "requires a finite, positive"):
            create_generator(config)


if __name__ == "__main__":
    unittest.main()
