/**
 * \file ParticleBomb.h
 *
 * \ingroup DLPGenerator
 * 
 * \brief Class def header for a class ParticleBomb
 *
 * @author drinkingkazu
 */

/** \addtogroup DLPGenerator

    @{*/
#ifndef __DLPGENERATOR_PARTICLEBOMB_H__
#define __DLPGENERATOR_PARTICLEBOMB_H__

#include <iostream>
#include <chrono>
#include <random>
#include "ParticleList.h"

namespace DLPGenerator {

  /**
     \class ParticleBomb
     User defined class ParticleBomb ... these comments are used to generate
     doxygen documentation!
  */
  class ParticleBomb{
    
  public:
    
    /// Default constructor
    ParticleBomb(int seed, bool debug=false)
    : _seed((unsigned int)(seed >= 0 ? seed : std::chrono::system_clock::now().time_since_epoch().count()))
    , _engine(_seed)
    , _flat_random(0.,1.)
    , _debug(debug)
    { this->Clear(); 
      if(_debug) std::cout << "ParticleBomb created with SEED " << _seed << std::endl << std::endl;
    }
    
    /// Default destructor
    ~ParticleBomb(){}

    /// returns seed
    unsigned int Seed() const { return _seed; }
    /// sets seed
    void   Seed(int seed);  
    /// sets debug mode
    void   Debug(bool debug) { _debug = debug; }
    /// Clears configuration
    void   Clear() { _param_v.clear(); _configured=false;}
    /// Add configuration
    void   Add(GenParamInteraction param);
    /// A sampler from uniform distribution
    double flat_dfire(double vmin, double vmax);
    /// A sampler from uniform distribution
    int    flat_ifire(int vmin, int vmax);
    /// Run the generator
    std::vector<std::vector<DLPGenerator::Particle> > Generate();
    /// Utility function to flatten the return of Generate, and outputs the HEPEVT format array
    std::vector<std::array<double,15> > Flatten(const std::vector<std::vector<DLPGenerator::Particle> >& particles) const;
    /// Utility function to print-out the particle hierarchy. The input is the flattned array
    void PrintHierarchy(const std::vector<std::array<double,15> >& particles) const;

  private:

    /// Determins which particle to produce
    std::vector<size_t> GenParticles(size_t num_part,
                                    const std::vector<GenParamParticle> param_v);
    /// Determines a particle position (uniform sampling)
    void   GenPosition(const GenParamInteraction& param, double& x, double& y, double& z, double& t);
    /// Determines a particle momentum (isotropic direction, uniform magnitude)
    void   GenMomentum(const GenParamParticle& param, Particle& part);

    /// random seed for the record
    unsigned int _seed;

    /// random number engine
    std::mt19937_64 _engine;
    // flat distribution
    std::uniform_real_distribution<double> _flat_random;

    /// array of particle info for generation
    std::vector<GenParamInteraction> _param_v;
    
    /// verbosity flag
    bool _debug;

    /// configuration flag
    bool _configured;
  };
}

#endif
/** @} */ // end of doxygen group 

