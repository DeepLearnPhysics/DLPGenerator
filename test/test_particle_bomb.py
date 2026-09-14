import unittest

from ROOT import DLPGenerator as G
from dlp_generator.config_parser import create_generator


def particle(pdg, multiplicity, weight=1.0):
    param = G.GenParamParticle()
    for code in pdg:
        param.pdg.push_back(code)
    param.multi[0], param.multi[1] = multiplicity
    param.kerange[0], param.kerange[1] = (0.0, 0.0)
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
