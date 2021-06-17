---
jupytext:
  cell_metadata_filter: -all
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.10.3
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Getting started

This note covers a brief overview of running `ParticleBomb`  event generator ([repository](https://github.com/DeepLearnPhysics/EventGenerator)), which is used for generating simulation samples to train data reconstruction models in `lartpc_mlreco3d` package ([repository](https://github.com/DeepLearnPhysics/lartpc_mlreco3d)). 

## What is an event generator?

In case you are not familiar with the term _event generator_, in High Energy Physics (HEP) experiments, an event generator is the first step of a simulation chain which consists of 3 major steps.

1. **Event Generator** ... generates a list of particles that will interact with an experiment detector. There are many event generators out there (e.g. GENIE, GLOBUS, GIBU, ...) but they all do the same: generate a list of particles.
  
2. **Particle Tracking** ... takes the output of 1 (i.e. a list of particles), and simulate how each particle interacts with the detector medium. For this stage, almost all HEP experiments use a software called Geant4, which contains detailed physics models of how all kinds of particles interact with all kinds of materials. The output of Geant4 is energy deposition information in the form of a particle trajectory. For instance, if your event generator provide 1 muon as an input to this stage of simulation, Geant4 simulates how this muon go through all kinds of micro-physics processes such as multiple coulomb scattering, radiation of another particle, an interaction with electromagnetic field, a decay, energy deposition along its trajectory in a medium, etc.. 

3. **Detector response** ... takes the energy deposition information from Geant4, and simulates how your detector respond to them. This may include how your detector signal is created (e.g. for LArTPC, this might be ionization electrons and scintillation photons), how those signal propagate to sensitive detector electronics, and how those electronics respond to the signal. The output of this stage mimics the data that is recorded by your detector.

## How to use ParticleBomb

This event generator can be run in 2+1 steps.

1. Instantiate and configure
2. Generate particles
3. Convert into HEPEVT-like format (optional)

The generation is done after the 2nd step. The 3rd step is optional to convert the results into a HEPEVT-friendly format, which is used to feed the output of this generator into the next step of simulation = particle tracking using Geant4. We go over the HEPEVT format later in this note.


### Step 1: instantiate and configure

The event generator package provides a utility Python function called `create_generator`. This function consumes a formatted configuration (Python `dict`), then create a `ParticleBomb` instance with the configuration parameters applied. 

In this note, we don't go over the configuration format. That will be [the next section](./Configuration.md). For now, we use an example configuration provided by the package.

```{code-cell}
import yaml
from dlp_generator import create_generator, EXAMPLE_CONFIG

# parse configuration
cfg=yaml.load(EXAMPLE_CONFIG, Loader=yaml.Loader)

# create and configure a generator
gen = create_generator(cfg)
```

### Step 2: run the generator

Just call `Generate` function :) 

```{code-cell}
# run the generator
result = gen.Generate()
```

Yep, that's it! But yeah, we don't feel like this meant anything real. So let's try one more time. This time, we enable a `Debug` flag so that the generator prints out some information as it runs.

```{code-cell}
# Set the Debug flag to True in the configuration
cfg['Debug'] = True

# create and configure a generator
gen = create_generator(cfg)

# run
result = gen.Generate()
```

... and now we can see information about particles generated. It feels a bit more real :) In the above example, we set the debug flag in the configuration dictionary. Another way to set/unset is to simply call an attribute function of the generator.

```{code-cell}
gen.Debug(False)
```

## Before step-3 ... HEPEVT format

A HEPEVT format is a way to list necessary information about particles to be simulated by Geant4, and it's pretty simple. For each particle, 15 values are recorded. It's actually an ASCII text file listing 15 values (=one particle information) per line. Values are separated by a space. Here're the list of values contained:

1. `status code` ... 1 = feed in Geant4, other values mean don't track (but useful for the record)
2. `PDG code` ... an identifier for a type of a particle. See [this reference](https://pdg.lbl.gov/2007/reviews/montecarlorpp.pdf) to decode.
3. Line number of the first parent particle (0 for initial entries)
4. Line number of the second parent particle
5. Line number of the first child particle
6. Line number of the last child particle
7. `x` momentum [GeV/c]
8. `y` momentum [GeV/c]
9. `z` momentum [GeV/c]
10. `energy` [GeV]
11. `mass` [GeV/c^2]
12. `x` position [mm]
13. `y` position [mm]
14. `z` position [mm]
15. `time` [ns]

For example, let's consider 2 particles:
* A muon at position (0,0,0), time=0, momentum (0,0,0) [GeV/c] with energy 105 GeV and mass 0.105 GeV/c^2
* A photon at position (1,1,1), time=0, momentum (1,0,0) with energy 1 GeV and mass 0 GeV/c^2

The HEPEVT format would look like this:
```
1 13 0 0 0 0 0 0 0 105 105 0 0 0 0
1 22 0 0 0 0 1 0 0 1   0   1 1 1 0
```

## Step-3: converting into HEPEVT-like format

So we would like to convert the resulting list of particles into HEPEVT format. `ParticleBomb` provides a utility function called `Flatten` to do this.

```{code-cell}
# Convert the result into HEPEVT-like format, which is an array of length-15-array
hepevt = gen.Flatten(result)
```

Let's loop over the list of particles and print out 15 attribute values

```{code-cell}
for part in hepevt:
    line = ''
    for v in part: line += str(v) + ' '
    print(line)
```

OK that's a nightmare (though you would need this for Geant4!). `ParticleBomb` also has a friendly function that prints out a formatted summary text showing a list of particle type and hierarchies.

```{code-cell}
# print out the hierarchy
gen.PrintHierarchy(hepevt)
```

## Reproducibility (seed)

Finally, when debugging, it's often useful to have a full reproducibility. This is possible by creating a generator with a fixed random number seed. The seed used by the generator is printed out at the creation when you enable the debug mode. Or you can also just ask for it.

```{code-cell}
print('Seed:',gen.Seed())
```

If the seed is not provided by the configuration, or provided as a negative value, the generator uses the timestamp as a seed, which changes all the time, in order to avoid always generating the same set of particles. Let's try running the generator twice with the time seed. We expect the generated particle list to be different.

```{code-cell}
gen.Seed(-1)
gen.PrintHierarchy(gen.Flatten(gen.Generate()))

gen.Seed(-1)
gen.PrintHierarchy(gen.Flatten(gen.Generate()))
```

When we debug the code, on the other hand, we often want to test the code behavior against a specific (fixed) state. We want a predictability in the output (to make sure it's working). For this, you can set the seed and have a reproducible set of particles.

```{code-cell}
gen.Seed(1)
gen.PrintHierarchy(gen.Flatten(gen.Generate()))

gen.Seed(1)
gen.PrintHierarchy(gen.Flatten(gen.Generate()))
```

Hopefully this note helped you to learn how to run the `ParticleBomb` event generator. In the next section, we go over how to configure the generator so that we can dictate what kind of particles to be generated.


