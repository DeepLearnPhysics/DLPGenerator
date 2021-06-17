/**
 * \file ParticleList.h
 *
 * \ingroup DLPGenerator
 * 
 * \brief Class def header for a class ParticleList
 *
 * @author drinkingkazu
 */

/** \addtogroup DLPGenerator

    @{*/
#ifndef __DLPGENERATOR_PARTICLELIST_H__
#define __DLPGENERATOR_PARTICLELIST_H__

#include <vector>
#include <array>
#include <limits>

namespace DLPGenerator {

  static const double kINVALID_DOUBLE = std::numeric_limits<double>::max();

  struct GenParamParticle {
    std::vector<int       > pdg;     /// a list of possible PDG code of a particle for generation
    std::array <size_t, 2 > multi;   /// multiplicity of this particle instance
    std::array <double, 2 > kerange; /// range of kinetic energy (or momentum, depending on use_mom flag)
    bool use_mom;  /// if true, kerange is interpreted as a momentum magnitude
    double weight; /// weight factor to produce this particle w.r.t. other instances

    GenParamParticle()
    {
      for(auto& v : multi) v = 0;
      for(auto& v : kerange) v = kINVALID_DOUBLE;
      use_mom = false;
      weight = -1;
    }
  };

  struct GenParamInteraction {
    std::array <size_t, 2> num_event;    /// the range of multiplicity of an interaction to be generated
    std::array <size_t, 2> num_particle; /// the range of multiplicity of particles per interaction
    std::array <double, 2> xrange;       /// the range of the vertex along x-axis
    std::array <double, 2> yrange;       /// the range of the vertex along y-axis
    std::array <double, 2> zrange;       /// the range of the vertex along z-axis
    std::array <double, 2> trange;       /// the range of the interaction in time
    std::vector<GenParamParticle> part_param_v; /// parameters of particles to be generated
    bool add_root; /// if true, add a graviton as a parent to help grouping particles

    GenParamInteraction()
    {
      for(auto& v : num_event    ) v = 0;
      for(auto& v : num_particle ) v = 0;
      for(auto& v : xrange ) v = kINVALID_DOUBLE;
      for(auto& v : yrange ) v = kINVALID_DOUBLE;
      for(auto& v : zrange ) v = kINVALID_DOUBLE;
      for(auto& v : trange ) v = kINVALID_DOUBLE;
      add_root = false;
    }
  };

  struct Particle{
    int status_code; 
    int pdg_code, parent0, parent1, child_first, child_last;
    double px, py, pz, energy, mass, x, y, z, t;

    Particle()
    { 
      pdg_code = 0;
      status_code = parent0 = parent1 = child_first = child_last = -1;
      px = py = pz = energy = mass = x = y = z = t = kINVALID_DOUBLE;
    }

  };
}

#endif
/** @} */ // end of doxygen group 

