#ifndef __DLPGENERATOR_PARTICLEBOMB_CXX__
#define __DLPGENERATOR_PARTICLEBOMB_CXX__

#include "ParticleBomb.h"
#include "TDatabasePDG.h"

namespace DLPGenerator {

	void   ParticleBomb::Seed(int seed) 
	{
		_seed = (unsigned int)(seed >= 0 ? seed : std::chrono::system_clock::now().time_since_epoch().count());
    	_engine = std::mt19937_64(_seed);  
	}

    void   ParticleBomb::Add(DLPGenerator::GenParamInteraction param) {

    	// Sanity check
    	try {
			if(param.num_event[0]>param.num_event[1]) throw 1;
			if(param.num_particle[0]>param.num_particle[1]) throw 2;
			if(param.xrange[0]>param.xrange[1]) throw 3;
			if(param.yrange[0]>param.yrange[1]) throw 4;
			if(param.zrange[0]>param.zrange[1]) throw 5;
			if(param.trange[0]>param.trange[1]) throw 6;
			if(param.part_param_v.empty()) throw 7;
			for(auto const& part : param.part_param_v) {
				if(part.multi[0]>part.multi[1]) throw 8;
				if(part.kerange[0]>part.kerange[1]) throw 9;
				if(part.weight<0) throw 10;
			}
		} catch (int error_code) {
			std::cerr << "Error in one of parameters: error code " << error_code << std::endl;
			std::cout << "Error codes meaning below...." << std::endl
			<< "  1  ... number of event is negative or the range is invalid" << std::endl
			<< "  2  ... number of particles per event is negative or the range is invalid " << std::endl
			<< "  3  ... the x range is invalid " << std::endl
			<< "  4  ... the y range is invalid " << std::endl
			<< "  5  ... the z range is invalid " << std::endl
			<< "  6  ... the t range is invalid " << std::endl
			<< "  7  ... the particle parameter list is empty" << std::endl
			<< "  8  ... the range of particle multiplicity per config is negative or the range is invalid " << std::endl
			<< "  9  ... the kinetic energy range is invalid" << std::endl
			<< "  10 ... the weight is negative value (invalid)" << std::endl;
			return;
		}
		_configured = true;
		_param_v.push_back(param);
    }

    std::vector<std::array<double,15> > 
    ParticleBomb::Flatten(const std::vector<std::vector<DLPGenerator::Particle> >& particles) const
    {
    	std::vector<std::array<double,15> > result;
    	for(auto const& part_v : particles) {
    		for(auto const& part : part_v) {
    			std::array<double,15> param;
    			param[0 ] = part.status_code;
    			param[1 ] = part.pdg_code;
    			param[2 ] = part.parent0;
    			param[3 ] = part.parent1;
    			param[4 ] = part.child_first;
    			param[5 ] = part.child_last;
    			param[6 ] = part.px;
    			param[7 ] = part.py;
    			param[8 ] = part.pz;
    			param[9 ] = part.energy;
    			param[10] = part.mass;
    			param[11] = part.x;
    			param[12] = part.y;
    			param[13] = part.z;
    			param[14] = part.t;
    			result.emplace_back(param);
    		}
    	}
    	return result;
    }

    void ParticleBomb::PrintHierarchy(const std::vector<std::array<double,15> >& particles) const 
    {

    	std::cout<< "Dumping hierarchy information for " << particles.size() << " particles..." << std::endl;
    	  	for(size_t idx=0; idx<particles.size(); ++idx) {
    		auto const& part = particles[idx];
    		if(idx == part[2]) {
    			std::cout << std::endl 
    				<< "  ---- Line " << idx << " PDG " << part[1] << " energy " << part[9] << " [GeV]";
    			if(part[5]>0)
    				std::cout << " ... " << part[5] - part[4] + 1 << " children particles";
    			std::cout << std::endl;
    		}else
    			std::cout << "    |- Line " << idx << " PDG " << part[1] << " energy " << part[9] 
    			<< " [GeV] ... parent " << part[2] << std::endl;
    	}
    	std::cout << std::endl;
    }



	double ParticleBomb::flat_dfire(double vmin, double vmax) {
		// return a floating point: vmin <= return <= vmax
		std::uniform_real_distribution<double> sample(vmin,vmax);
		return sample(_engine);
	}

	int ParticleBomb::flat_ifire(int vmin, int vmax) {
		// return an integer: vmin <= return <= vmax
		std::uniform_int_distribution<int> sample(vmin,vmax);
		return sample(_engine);
	}


	std::vector<std::vector<DLPGenerator::Particle> > ParticleBomb::Generate() {

		// create the result
	    std::vector<std::vector<DLPGenerator::Particle> > result;

		// make sure the generator is configured
		if (!_configured) {
			std::cerr << "Parameters not yet configured..." << std::endl;
			return result;
		}

	    if(_debug>0) std::cout << "Running a new generation..." << std::endl;


		for(size_t cfg_idx=0; cfg_idx < _param_v.size(); ++cfg_idx) {

			auto const& int_param = _param_v[cfg_idx];

			// Decide the multiplicity to run
			const int num_int = this->flat_ifire(int_param.num_event[0],int_param.num_event[1]);

			if(_debug) std::cout << std::endl << std::endl
				<< "Interaction config " << cfg_idx 
				<< " multiplicity: " << num_int << std::endl;


			// Generate each interactions
			int num_int_generated = 0;
			while(num_int > num_int_generated) {

				// Decide number of particles to be generated
			    int num_part = this->flat_ifire(int_param.num_particle[0],int_param.num_particle[1]);

			    if(_debug) std::cout << std::endl << "  Generating an interaction " << num_int_generated 
			    	<< " with " 
			    	<< num_part << " particles..." << std::endl;

			    // Decide the interaction vertex
			    double x,y,z,t;
			    this->GenPosition(int_param, x, y, z, t);

			    // Decide which particles to be generated
			    auto order_list = this->GenParticles(num_part, int_param.part_param_v);

			    // Generate particles
			    std::vector<DLPGenerator::Particle> part_v;
			    part_v.reserve(order_list.size()+1);

			    // Add graviton as a virtual parent if requested
			    if(int_param.add_root) {
			    	if(_debug) std::cout << "  Adding a virtual root particle (Graviton PDG 39)" << std::endl;
			    	DLPGenerator::Particle graviton;
			    	graviton.status_code = 3;
			    	graviton.pdg_code = 39;
					graviton.mass = graviton.energy = graviton.px = graviton.py = graviton.pz = 0.;
					part_v.emplace_back(graviton);
			    }

			    for(auto const& idx : order_list) {

			    	// generation parameter set
			    	auto const& part_param = int_param.part_param_v.at(idx);

			    	// create an instance
			    	Particle part;

			    	// set unique attributes
			    	if(part_param.pdg.size() > 1)
		    	        part.pdg_code = part_param.pdg[this->flat_ifire(0,part_param.pdg.size()-1)];
		    	    else
		    	    	part.pdg_code = part_param.pdg[0];
					part.mass = TDatabasePDG::Instance()->GetParticle(part.pdg_code)->Mass();
					part.x = x;
					part.y = y;
					part.z = z;
					part.t = t;

					if(_debug) std::cout << std::endl
						<< "    New particle PDG " << part.pdg_code 
						<< " Mass " << part.mass 
						<< " [GeV/c**2]" << std::endl;

			    	// set momentum
			    	this->GenMomentum(part_param, part);

			    	// save a particle
			    	part_v.emplace_back(part);

			    } // done generating particles for an interaction

			    // If the virtual parent is added, sum the energy and momentum
			    if(int_param.add_root) {
			    	auto& graviton = part_v.at(0);
			    	for(size_t part_idx=1; part_idx<part_v.size(); ++part_idx) {
			    		auto const& part = part_v.at(part_idx);
						graviton.energy += part.energy;
						graviton.px += part.px;
						graviton.py += part.py;
						graviton.pz += part.pz;
						graviton.x = part.x;
						graviton.y = part.y;
						graviton.z = part.z;
						graviton.t = part.t;
					}
			    }

			    // save an interaction
			    result.emplace_back(part_v);
			    
				num_int_generated++;

			}// done generating num_int interactions


		}// done looping over GenParamInteraction list

		/*
		 Now set parent/child IDs. Some assumptions here
			- for an interaction with only 1 particle, set parent = itself
			- for an interaction with >1 particles, [1] insert a graviton (hell yeah)
			  as a parent, purely for grouping purpose.
		*/
		size_t part_index = 0;

		for(auto& part_v : result) {

			if(part_v.empty()) continue;

			if(part_v.front().pdg_code == 39) {
				// virtual root particle exists. Set graviton's IDs
				auto& graviton = part_v.front();
				graviton.parent0 = part_index;
				graviton.parent1 = part_index;
				graviton.child_first = part_index+1;
				graviton.child_last  = part_index+(part_v.size()-1);
				
				// now set particle ids
				for(size_t idx=1; idx<part_v.size(); ++idx) {
					auto& part = part_v[idx];
					part.status_code = 1;
					part.parent0 = part_index;
					part.parent1 = part_index;
					part.child_first = 0;
					part.child_last  = 0;
				}
				// increment the part_index
				part_index += part_v.size();
			}

			else{
				for(auto& part : part_v) {
					part.status_code = 1;
					part.parent0 = part_index;
					part.parent1 = part_index;
					part.child_first = 0;
					part.child_last  = 0;
					// increment the part_index
					part_index +=1;
				}
			}

		}// done looping over the result

		return result;
	}


	std::vector<size_t> ParticleBomb::GenParticles(size_t num_part,
		const std::vector<GenParamParticle> param_v) 
	{
	    
	    std::vector<size_t> result;
	    std::vector<size_t> gen_count_v(param_v.size(),0);
	    std::vector<double> weight_v(param_v.size(),0);
	    for(size_t idx=0; idx<param_v.size(); ++idx)
	        weight_v[idx] = param_v[idx].weight;
	    	    
	    while(num_part) {
	        
	        double total_weight = 0;
	        for(auto const& v : weight_v) total_weight += v;
	        
	        double rval = 0;
	        rval = this->flat_dfire(0,total_weight);
	        
	        size_t idx = 0;
	        for(idx = 0; idx < weight_v.size(); ++idx) {
	            rval -= weight_v[idx];
	            if(rval <=0.) break;
	        }
	        
	        // register to the output
	        result.push_back(idx);
	        
	        // if generation count exceeds max, set probability weight to be 0
	        gen_count_v[idx] += 1;
	        if(gen_count_v[idx] >= param_v[idx].multi[1])
	            weight_v[idx] = 0.;
	        
	        --num_part;
	    }
	    return result;
	}

	void ParticleBomb::GenPosition(const GenParamInteraction& param, double& x, double& y, double& z, double& t) 
	{
		x = this->flat_dfire(param.xrange[0],param.xrange[1]);
		y = this->flat_dfire(param.yrange[0],param.yrange[1]);
		z = this->flat_dfire(param.zrange[0],param.zrange[1]);
		t = this->flat_dfire(param.trange[0],param.trange[1]);


		if(_debug>0) {
		  std::cout << "  Vertex at (" 
		  << x << "," << y << "," << z << ") [mm] ... time @ " << t << " [ns]" << std::endl;
		}
	}

	void ParticleBomb::GenMomentum(const GenParamParticle& param, Particle& part) 
	{	    
		assert(part.mass != kINVALID_DOUBLE);

	    part.energy = 0;
	    if(param.use_mom)
	        part.energy = sqrt(pow(this->flat_dfire(param.kerange[0],param.kerange[1]),2) + pow(part.mass,2));
	    else
	        part.energy = this->flat_dfire(param.kerange[0],param.kerange[1]) + part.mass;
	    
	    double mom_mag = sqrt(pow(part.energy,2) - pow(part.mass,2));

	    double phi   = this->flat_dfire(0, 2 * 3.141592653589793238);
	    double theta = this->flat_dfire(0, 1 * 3.141592653589793238);
	      
	    part.px = cos(phi) * sin(theta);
	    part.py = sin(phi) * sin(theta);
	    part.pz = cos(theta);
	    
	    if(_debug)
	        std::cout << "    Direction : (" << part.px << "," << part.py << "," << part.pz << ")" << std::endl
	        << "    Momentum  : " << mom_mag << " [GeV/c]" << std::endl
	        << "    Energy    : " << part.energy << " [GeV/c**2]" << std::endl;
	    part.px *= mom_mag;
	    part.py *= mom_mag;
	    part.pz *= mom_mag;
	    
	}

	
}

#endif
