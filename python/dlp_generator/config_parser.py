
from ROOT import DLPGenerator as G
import yaml

def create_generator(cfg):
	'''
	Parse configure ParticleBomb event generator, and return the instance.
	For an example configuration yaml text, see at the bottom of config_parser.py.
	ARG:
	  cfg_txt - a configuration dictionary.
	RETURN:
	  ParticleBomb event generator with a configuration applied
	'''

	# create ParticleBomb instance (optionally with SEED and Debug options)
	gen = G.ParticleBomb(cfg.get('SEED',-1),cfg.get('Debug',False))

	# Add interaction config blocks to the generator
	for key,val in cfg.items():

		# Ignore SEED and Debug configs that are already consumed
	    if key in ['SEED','Debug']: continue
	    # Sanity check, everything else should be an interaction config
	    if not type(val) == type(dict()):
	    	print('Unexpected key-value pair from the config...')
	    	print('Key:',key)
	    	print('Value:',val)
	    	raise ValueError 
	    # Create an interaction config parameter set to be filled
	    param = G.GenParamInteraction()
	    # Fill interaction configs. See ParticleList.h for the attributes.
	    param.num_event[0],param.num_event[1] = val['NumEvent']
	    param.num_particle[0],param.num_particle[1] = val['NumParticle']
	    param.xrange[0],param.xrange[1] = val['XRange']
	    param.yrange[0],param.yrange[1] = val['YRange']
	    param.zrange[0],param.zrange[1] = val['ZRange']
	    param.trange[0],param.trange[1] = val['TRange']
	    param.add_root = val.get('AddParent',False)
	    # Fill particle-wise config parameter set
	    for part in val['Particles']:
	        part_param = G.GenParamParticle()
	        # Fill particle configs. See ParticleList.h for the attributes.
	        for pdg in part['PDG']: part_param.pdg.push_back(pdg)
	        part_param.multi[0],part_param.multi[1] = part['NumRange']
	        part_param.kerange[0],part_param.kerange[1] = part['KERange']
	        part_param.use_mom = part.get('UseMom',part_param.use_mom)
	        part_param.weight = part.get('Weight')
	        # Add this particle config to an interaction config
	        param.part_param_v.push_back(part_param)

	    # Add the interaction config to the generator
	    gen.Add(param)

	# return the generator instance
	return gen
    

# Example configuration yaml text
EXAMPLE_CONFIG = '''
SEED: -1

GeneratorMPV:
  NumEvent: [1,2]
  NumParticle: [3,3]
  XRange: [0,100]
  YRange: [0,100]
  ZRange: [0,100]
  TRange: [0,10]
  AddParent: True
  Particles:
    -
      PDG:      [11,13]
      NumRange: [1,1]
      KERange:  [0,1]
      UseMom:   False
      Weight:   1

    -
      PDG:      [211,-211]
      NumRange: [0,2]
      KERange:  [0,1]
      UseMom:   False
      Weight:   1
      
    -
      PDG:      [22,111]
      NumRange: [0,2]
      KERange:  [0,1]
      UseMom:   False
      Weight:   1
      
    -
      PDG:      [2112]
      NumRange: [0,2]
      KERange:  [0,1]
      UseMom:   False
      Weight:   1
      
GeneratorMPR:
  NumEvent: [1,1]
  NumParticle: [1,5]
  XRange: [0,100]
  YRange: [0,100]
  ZRange: [0,100]
  TRange: [0,10]
  Particles:
    -
      PDG:      [13]
      NumRange: [0,5]
      KERange:  [0,1]
      UseMom:   False
      Weight:   8

    -
      PDG:      [11]
      NumRange: [0,5]
      KERange:  [0,1]
      UseMom:   False
      Weight:   1
      
    -
      PDG:      [2112]
      NumRange: [0,5]
      KERange:  [0,1]
      UseMom:   False
      Weight:   1
        
'''

if __name__ == '__main__':

	# parse configuration
	cfg=yaml.load(EXAMPLE_CONFIG, Loader=yaml.Loader)

	# for testing, set Debug to True
	cfg['Debug'] = True

	# create and configure a generator
	gen = create_generator(cfg)

	# run the generator
	result = gen.Generate()

	# print out the hierarchy
	gen.PrintHierarchy(gen.Flatten(result))
