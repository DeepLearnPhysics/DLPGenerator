//
// cint script to generate libraries
// Declaire namespace & classes you defined
// #pragma statement: order matters! Google it ;)
//

#ifdef __CINT__
#pragma link off all globals;
#pragma link off all classes;
#pragma link off all functions;

#pragma link C++ namespace DLPGenerator+;
#pragma link C++ class DLPGenerator::ParticleBomb+;
#pragma link C++ struct DLPGenerator::GenParamInteraction+;
#pragma link C++ struct DLPGenerator::GenParamParticle+;
#pragma link C++ class std::vector<DLPGenerator::GenParamParticle>+;
#pragma link C++ struct DLPGenerator::Particle+;
#pragma link C++ class std::vector<DLPGenerator::Particle>+;
#pragma link C++ class std::vector<std::vector<DLPGenerator::Particle> >+;
//ADD_NEW_CLASS ... do not change this line
#endif


