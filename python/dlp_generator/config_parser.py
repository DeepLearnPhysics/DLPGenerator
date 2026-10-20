
from ROOT import DLPGenerator as G
import math
import yaml

def parse_shoot_inward(value):
	'''
	Interpret the ShootInward config value and return the bias exponent.
	It is either a boolean (True selects the default strength, False disables the
	bias) or a non-negative number that sets the strength directly, where 0 is
	equivalent to False. See ParticleList.h for how the exponent is applied.
	'''
	# bool is a subclass of int, so it has to be tested first
	if isinstance(value, bool):
		return 1.0 if value else 0.0
	if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
		raise ValueError(
			'ShootInward must be a boolean or a non-negative number, got %r' % (value,)
		)
	return float(value)

def configure_boost(param, boost):
	"""Validate the optional interaction boost and populate its C++ ranges."""
	if not isinstance(boost, dict):
		raise ValueError('Boost must be a mapping')
	allowed = {'BetaGammaRange', 'PhiRange', 'ThetaRange', 'Direction'}
	if set(boost) - allowed:
		raise ValueError('Unknown Boost keys: %s' % (set(boost) - allowed,))
	if 'BetaGammaRange' not in boost:
		raise ValueError('Boost requires BetaGammaRange')

	def finite_number(value):
		return (not isinstance(value, bool) and isinstance(value, (int, float))
		        and math.isfinite(value))

	def bounds(name, default, maximum):
		value = boost.get(name, default)
		if (not isinstance(value, (list, tuple)) or len(value) != 2
		    or not all(finite_number(v) for v in value)
		    or not 0 <= value[0] <= value[1] <= maximum):
			raise ValueError('Boost.%s must be a finite, ordered, non-negative pair within %s' % (name, maximum))
		return value

	param.boost_betagamma_range[0], param.boost_betagamma_range[1] = bounds(
		'BetaGammaRange', None, float('inf'))
	phi = bounds('PhiRange', [0., 2.*math.pi], 2.*math.pi)
	theta = bounds('ThetaRange', [0., math.pi], math.pi)
	if 'Direction' in boost:
		if 'PhiRange' in boost or 'ThetaRange' in boost:
			raise ValueError('Boost.Direction cannot be combined with PhiRange or ThetaRange')
		direction = boost['Direction']
		if (not isinstance(direction, (list, tuple)) or len(direction) != 3
		    or not all(finite_number(v) for v in direction)):
			raise ValueError('Boost.Direction must be a finite nonzero three-vector')
		scale = max(abs(v) for v in direction)
		if scale == 0:
			raise ValueError('Boost.Direction must be a finite nonzero three-vector')
		x, y, z = (v / scale for v in direction)
		angle_phi = math.atan2(y, x) % (2.*math.pi)
		angle_theta = math.atan2(math.hypot(x, y), z)
		phi = [angle_phi, angle_phi]
		theta = [angle_theta, angle_theta]
	param.boost_phi_range[0], param.boost_phi_range[1] = phi
	param.boost_theta_range[0], param.boost_theta_range[1] = theta

def create_generator(cfg):
	'''
	Parse configure ParticleBomb event generator, and return the instance.
	For an example configuration yaml text, see at the bottom of config_parser.py.
	ARG:
	  cfg_txt - a configuration dictionary.
	RETURN:
	  ParticleBomb event generator with a configuration applied
	'''
	if 'InteractionSelection' in cfg:
		from .interaction_selector import create_interaction_selector
		return create_interaction_selector(cfg, create_generator)

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
	    param.shoot_inward_power = parse_shoot_inward(val.get('ShootInward',False))
	    strict = val.get('ShootInwardStrict', False)
	    if not isinstance(strict, bool):
	        raise ValueError('ShootInwardStrict must be a boolean, got %r' % (strict,))
	    param.shoot_inward_strict = strict
	    if 'Boost' in val:
	        configure_boost(param, val['Boost'])
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
