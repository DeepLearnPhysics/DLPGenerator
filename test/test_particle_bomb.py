import unittest

from ROOT import DLPGenerator as G


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


if __name__ == "__main__":
    unittest.main()
