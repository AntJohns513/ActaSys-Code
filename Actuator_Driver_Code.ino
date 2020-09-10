#include <Audio.h>
#include <Wire.h>
#include <EEPROM.h>

const float max_amplitude = 0.91; //Maximum ampltidue allowed by teensy/piezos

float ramp_time = 2.0;  //Time the actuator takes to ramp up to voltage

bool run_waveform = false;

float channel1_amp = 0;
float channel1_freq = 0;

int ramp_steps = 50;

int Serial_on = 0;

int ledPin = 13;

// Feedback
int channel1_sense = 12;
int Teensy_status = 0;
int reset_flag = 0;
int failure_flag = 0;
int decrease_volt = 0;

int maximum_overdrive = 14;

// Audio Library Setup
AudioSynthWaveformSine * pSine1;      //xy=106,142
AudioSynthWaveform * pWaveform1;      //xy=125,71
AudioEffectMultiply * pMultiply1;     //xy=393,146
AudioOutputAnalogStereo * pDacs1;     //xy=623,157

AudioConnection * pPatchCord1; // patchCord1(sine1, 0, multiply1, 1);
AudioConnection * pPatchCord2; // patchCord2(waveform1, 0, multiply1, 0);
AudioConnection * pPatchCord3; // patchCord3(multiply1, 0, dacs1, 0);
AudioConnection * pPatchCord4;
AudioConnection * pPatchCord5;

int16_t arbitrary_wave[256];
int16_t arbitrary_wave2[] = { 0,   804,  1608,  2410,  3212,  4011,  4808,  5602,  6393,  7179,
                              7962,  8739,  9512, 10278, 11039, 11793, 12539, 13279, 14010, 14732,
                              15446, 16151, 16846, 17530, 18204, 18868, 19519, 20159, 20787, 21403,
                              22005, 22594, 23170, 23731, 24279, 24811, 25329, 25832, 26319, 26790,
                              27245, 27683, 28105, 28510, 28898, 29268, 29621, 29956, 30273, 30571,
                              30852, 31113, 31356, 31580, 31785, 31971, 32137, 32285, 32412, 32521,
                              32609, 32678, 32728, 32757, 32767, 32757, 32728, 32678, 32609, 32521,
                              32412, 32285, 32137, 31971, 31785, 31580, 31356, 31113, 30852, 30571,
                              30273, 29956, 29621, 29268, 28898, 28510, 28105, 27683, 27245, 26790,
                              26319, 25832, 25329, 24811, 24279, 23731, 23170, 22594, 22005, 21403,
                              20787, 20159, 19519, 18868, 18204, 17530, 16846, 16151, 15446, 14732,
                              14010, 13279, 12539, 11793, 11039, 10278,  9512,  8739,  7962,  7179,
                              6393,  5602,  4808,  4011,  3212,  2410,  1608,   804,     0,  -804,
                              -1608, -2410, -3212, -4011, -4808, -5602, -6393, -7179, -7962, -8739,
                              -9512, -10278, -11039, -11793, -12539, -13279, -14010, -14732, -15446, -16151,
                              -16846, -17530, -18204, -18868, -19519, -20159, -20787, -21403, -22005, -22594,
                              -23170, -23731, -24279, -24811, -25329, -25832, -26319, -26790, -27245, -27683,
                              -28105, -28510, -28898, -29268, -29621, -29956, -30273, -30571, -30852, -31113,
                              -31356, -31580, -31785, -31971, -32137, -32285, -32412, -32521, -32609, -32678,
                              -32728, -32757, -32767, -32757, -32728, -32678, -32609, -32521, -32412, -32285,
                              -32137, -31971, -31785, -31580, -31356, -31113, -30852, -30571, -30273, -29956,
                              -29621, -29268, -28898, -28510, -28105, -27683, -27245, -26790, -26319, -25832,
                              -25329, -24811, -24279, -23731, -23170, -22594, -22005, -21403, -20787, -20159,
                              -19519, -18868, -18204, -17530, -16846, -16151, -15446, -14732, -14010, -13279,
                              -12539, -11793, -11039, -10278, -9512, -8739, -7962, -7179, -6393, -5602,
                              -4808, -4011, -3212, -2410, -1608,  -804
                            };


//Values for the Main Wave
int carrier_wave_type = 0;  //0 for sinusoid and 1 for square wave
float carrier_freq = 200;  //Frequency of main wave (under 1000)
float carrier_amp = 0.5;   //Amplitude of main wave (0.##)
float carrier_sym = 0.5;   //Symmetry of main wave (0.##)

//Pulse Modulation Values
int pulse_modulation = 0;     //Initialized to 0 (off) set to 1 to turn on
int pulse_wave_type = 0;      //1 for Trapezoidal and 2 for Sinusoidal
float pulse_duty_cycle = 0.1; //Duty Cycle for Pulse Modulation (0.##)
int pulse_freq = 20;          //Modulation Frequency (under 100)
int pulse_rise_time = 10;     //Modulation rise time for Trapezoid (under 100)

//Sweeping Frequency Values
int sweep = 0;              //Initialized to 0 (off) set to 1 to turn on
int sweep_start_freq = 200; //Stat Sweep Frequency (under 1000)
int sweep_end_freq = 200;   //Final Sweep Frequency (under 1000)
int sweep_time = 30;        //Sweep time in seconds (under 100)

//Random Frequency Jumping Values
int random_freq_jump = 0;     //Initialized to 0 (off) set to 1 to turn on
int random_freq_jump_max = 0; //Maximum Frequency Jump (under 1000)
int random_freq_cycles = 1;   //Number of cycles before jumping frequency (under 100)

//Random Amplitude Jumping Values
int random_amp_jump = 0;        //Initialized to 0 (off) set to 1 to turn on
float random_amp_jump_max = 0;  //Maximum Amplitude Jump (#.#)
int random_amp_cycles = 1;      //Number of cycles before jumping amplitude (under 100)

//Weighted Frequency Jumping Values
int num_of_bounds = 0;        //Number of different bounding ranges (under 10)
int weighted_freq_cycles = 1; //Number of cycles before jumping frequency (under 100)
int* weighted_lower_bounds;   //Array of lower bounds for each range (each under 100)
int* weighted_upper_bounds;   //Array of upper bounds for each range (each under 100)
int* weighted_amounts;        //Array of the weights for each range (each under 10)

void update_values() {
  String str = Serial.readString();
  Serial.println("Values received: " + str);

  if (str.substring(0, 1) == 1) {
    run_waveform = true;
  } else {
    run_waveform = false;
    return;
  }

  int c = str.indexOf('c'); //Start of Carrier Wave params
  int p = str.indexOf('p'); //Start of Pulse Modulation params
  int s = str.indexOf('s'); //Start of Sweeping params
  int f = str.indexOf('f'); //Start of Frequency Jumping params
  int a = str.indexOf('a'); //Start of Amplitude Jumping params
  int w = str.indexOf('w'); //Start of Weighted Frequency params

  carrier_wave_type = str.substring(c + 1, c + 2).toInt();
  carrier_freq = str.substring(c + 2, c + 5).toInt();
  carrier_amp = str.substring(c + 5, c + 9).toFloat();
  carrier_sym = str.substring(c + 9, c + 13).toFloat();

  pulse_modulation = str.substring(p + 1, p + 2).toInt();
  if (pulse_modulation == 1) {
    pulse_wave_type = str.substring(p + 2, p + 3).toInt();
    pulse_duty_cycle = str.substring(p + 3, p + 7).toFloat();
    pulse_freq = str.substring(p + 7, p + 9).toInt();
    pulse_rise_time = str.substring(p + 9, p + 11).toInt();
  }

  sweep = str.substring(s + 1, s + 2).toInt();
  if (sweep == 1) {
    sweep_start_freq = str.substring(s + 2, s + 5).toInt();
    sweep_end_freq = str.substring(s + 5, s + 8).toInt();
    sweep_time = str.substring(s + 8, s + 10).toInt();
  }

  random_freq_jump = str.substring(f + 1, f + 2).toInt();
  if (random_freq_jump == 1) {
    random_freq_cycles = str.substring(f + 2, f + 4).toInt();
    random_freq_jump_max = str.substring(f + 4, f + 7).toInt();
  }

  random_amp_jump = str.substring(a + 1, a + 2).toInt();
  if (random_amp_jump == 1) {
    random_amp_cycles = str.substring(a + 2, a + 4).toInt();
    random_amp_jump_max = str.substring(a + 4, a + 8).toFloat();
  }

  if (num_of_bounds > 0){
    delete weighted_lower_bounds;
    delete weighted_upper_bounds;
    delete weighted_amounts;
  }

  num_of_bounds = str.substring(w+1, w+2).toInt();
  weighted_freq_cycles = str.substring(w+2, w+4).toInt();
  if (num_of_bounds > 0){
    weighted_lower_bounds = new int[num_of_bounds];
    weighted_upper_bounds = new int[num_of_bounds];
    weighted_amounts = new int[num_of_bounds];
    for (int i = 0; i < num_of_bounds; ++i){
      weighted_lower_bounds[i] = str.substring(w+4+(7*i), w+7+(7*i)).toInt();
      weighted_upper_bounds[i] = str.substring(w+7+(7*i), w+10+(7*i)).toInt();
      weighted_amounts[i] = str.substring(w+10+(7*i), w+11+(7*i)).toInt();
    }
  }
}

void setup() {
  if (Serial_on) {
    Serial.begin(115200);
  }

  AudioMemory(40);

  pSine1 = new AudioSynthWaveformSine();
  pWaveform1 = new AudioSynthWaveform();
  pMultiply1 = new AudioEffectMultiply();

  pDacs1 = new AudioOutputAnalogStereo();

  pPatchCord5 = new AudioConnection(*pSine1, 0, *pDacs1, 0);
  pPatchCord1 = new AudioConnection(*pSine1, 0, *pMultiply1, 1);
  pPatchCord2 = new AudioConnection(*pWaveform1, 0, *pMultiply1, 0);
  pPatchCord3 = new AudioConnection(*pMultiply1, 0, *pDacs1, 0);

  //modulationWaveform(pulse_duty_cycle, pulse_rise_time, pulse_wave_type);

  //pulseMode1(pulse_modulation);

  AudioInterrupts();

  pinMode(ledPin, OUTPUT);
  pinMode(channel1_sense, INPUT);
  pinMode(maximum_overdrive, INPUT);
  digitalWrite(ledPin, LOW);
  delay(2000);
  resetValues();
}

void modulationWaveform(float on_time, float rise_time, int wave_type) {
  // Calling this specifies the modulation waveform
  // Mode 1: trapezoidal modulation wave
  // Mode 2: Sinusoidal modulation
  // TO DO - Smoothed trapezoid modulation
  // TO DO - Add control to specify modulation on both channels

  float off_time = 1 - (on_time + 2 * rise_time);

  int t1 = int(256 * off_time / 2);
  int t2 = int(t1 + rise_time * 256);
  int t3 = int(t2 + on_time * 256);
  int t4 = int(t3 + rise_time * 256);

  switch (wave_type) {

    case 1: {
        for (int i = 0; i < 256; i++) {
          if (i <= t1) {
            arbitrary_wave[i] = 0;
          }
          else if (i < t2) {
            arbitrary_wave[i] = int((i - t1) * (pow(2, 15) - 1) / (t2 - t1));
          }
          else if (i <= t3) {
            arbitrary_wave[i] = pow(2, 15) - 1;
          }
          else if (i <= t4) {
            arbitrary_wave[i] = int((t4 - i) * (pow(2, 15) - 1) / (t4 - t3));
          }
          else {
            arbitrary_wave[i] = 0;
          }
        }
    } case 2: {
        for (int i = 0; i < 256; i++) {
          arbitrary_wave[i] = arbitrary_wave2[i];
        }
      }
  }
}

void rampOutput(float amplitude, float ramp_time, int ramp_steps, int phase) {
  // Changes output, ramping steadily
  // TO DO - adjust when both channels make a change so the changes occur proportionally

  int adjust_steps;
  float adjust_time;

  if (amplitude > max_amplitude) {
    amplitude = max_amplitude;
  }

  if (amplitude < 0) {
    amplitude = 0;
  }

  //AudioNoInterrupts();

  adjust_steps = ceil(ramp_steps * float(abs(amplitude - channel1_amp)) / float(max_amplitude));
  adjust_time = ramp_time * abs(amplitude - channel1_amp) / max_amplitude;
  for (int i = 0; i <= adjust_steps; i++) {
    pSine1->amplitude(channel1_amp + ((amplitude - channel1_amp)*i / adjust_steps));
    delay(int(adjust_time * 1000 / float(adjust_steps)));
  }
  channel1_amp = amplitude;
}

void pulseMode1(int mode) {
  // Changes channels from continuous sine waveform to a pulse modulated waveform
  // Utilizes connect/disconnect AudioStream.h/AudioStream.cpp updates thanks to
  // Borgert van der Kluit (b0rg3rt)
  // TO DO - Expand function to allow pulse control of both channels

  pSine1->frequency(carrier_freq);
  pSine1->amplitude(channel1_amp);

  if (mode == 1) {

    pPatchCord5->disconnect();

    pPatchCord1->connect();
    pPatchCord2->connect();
    pPatchCord3->connect();

    pWaveform1->arbitraryWaveform(arbitrary_wave, 100);
    pWaveform1->begin(1, pulse_freq, WAVEFORM_ARBITRARY);
  }

  if (mode == 0) {
    pPatchCord1->disconnect();
    pPatchCord2->disconnect();
    pPatchCord3->disconnect();

    pPatchCord5->connect();
  }

}

void rampFrequency(float frequency, float ramp_time, int step_size) {
  // Changes output, ramping steadily
  // TO DO - adjust when both channels make a change so the changes occur proportionally

  int adjust_freq;
  int ramp_steps;

  ramp_steps = ceil(abs(frequency - channel1_freq) / step_size);
  for (int i = 0; i <= ramp_steps; i++) {
    adjust_freq = int(channel1_freq + ((frequency - channel1_freq) * i / ramp_steps));
    if ((adjust_freq > frequency) && ((frequency - channel1_freq) > 0)) {
      adjust_freq = frequency;
    }
    else if ((adjust_freq < frequency) && ((frequency - channel1_freq) < 0)) {
      adjust_freq = frequency;
    }
    pSine1->frequency(adjust_freq);
    delay(int(ramp_time * 1000 / float(ramp_steps)));
  }
  channel1_freq = frequency;
}

void createRandomFreqWave(float frequency, int max_jump, int cycle_num)
{
  if (channel1_freq == 0 || channel1_amp == 0){
    channel1_freq = carrier_freq;
    pSine1->frequency(carrier_freq);
    rampOutput(carrier_amp, 3, 50, 0);
  }
  Serial.println("Max Jump: " + String(max_jump));
  Serial.println("Frequency: " + String(frequency));
  if (max_jump > frequency){
    max_jump = frequency;
  }
  while (run_waveform) {
    long jump_value = random((frequency-max_jump), (frequency+max_jump));
    pSine1->frequency(jump_value);
    channel1_freq = jump_value;
    delay(cycle_num * int(float(1000) / float(jump_value)));
    if (Serial.available()){
      update_values();
    }
  }
  resetValues();
}

void createRandomAmpWave(float amplitude, int max_jump, int cycle_num)
{
  if (channel1_freq == 0 || channel1_amp == 0){
    channel1_freq = carrier_freq;
    pSine1->frequency(carrier_freq);
    rampOutput(carrier_amp, 3, 50, 0);
  }
  float amp_min = amplitude - max_jump;
  float amp_max = amplitude + max_jump;
  if (amp_max > max_amplitude){
    amp_max = max_amplitude;
  }
  if (amp_min < 0){
    amp_min = 0;
  }
  while (run_waveform) {
    long jump_value = random((amp_min), (amp_max));
    pSine1->amplitude(jump_value);
    channel1_amp = jump_value;
    delay(cycle_num * int(float(1000) / float(carrier_freq)));
    if (Serial.available()){
      update_values();
    }
  }
  resetValues();
}

void createWeightedFreqWave(int num, int* lower_bounds, int* upper_bounds, int* weights, int cycle_num){
  if (channel1_freq == 0 || channel1_amp == 0){
    channel1_freq = carrier_freq;
    pSine1->frequency(carrier_freq);
    rampOutput(carrier_amp, 3, 50, 0);
  }
  int total_weight = 0;

  int i;
  for(i = 0; i < num; ++i){
    total_weight += weights[i];
  }
  
  while (run_waveform) {
    long rand_val = random(0, total_weight);
    int running_weight_sum = 0;
    
    for(i = 0; i < num; ++i){
      running_weight_sum += weights[i];
      if (running_weight_sum > rand_val){
        break;
      }
    }

    rand_val = random((lower_bounds[i]), (upper_bounds[i]));
    
    pSine1->frequency(rand_val);
    channel1_amp = rand_val;
    delay(cycle_num * int(float(1000) / float(rand_val)));
    if (Serial.available()){
      update_values();
    }
  }
  resetValues();
}


void createSweepWave(int freq_min, int freq_max, int sweep_time)
{
  if (channel1_freq == 0 || channel1_amp == 0){
    channel1_freq = freq_min;
    pSine1->frequency(freq_min);
    rampOutput(carrier_amp, 3, 50, 0);
  }
  
  int current_freq;
  current_freq = freq_min;

  int num_cycles = sweep_time * (freq_min + freq_max) / 2;

  int freq_steps = (freq_max - freq_min) / num_cycles;

  bool sweeping_up = true;

  while (run_waveform) {
    pSine1->frequency(current_freq);
    channel1_freq = current_freq;
    delay(int(float(num_cycles)*float(1000) / float(current_freq)));
    
    if (sweeping_up){
      current_freq += freq_steps;
    } else {
      current_freq -= freq_steps;
    }
    
    if (current_freq > freq_max){
      sweeping_up = false;
      current_freq = freq_max;
    } else if (current_freq < freq_min){
      sweeping_up = true;
      current_freq = freq_min;
    }
    
    if (Serial.available()){
      update_values();
    }
  }
  resetValues();
}

void resetValues(){
  pSine1->frequency(0);
  pSine1->amplitude(0);
  carrier_freq = 0;
  carrier_amp = 0;
  channel1_amp = 0;
  channel1_freq = 0;
}

void loop() {
  if (Serial.available()){
    update_values();
    if (run_waveform) {
      if (pulse_modulation == 1) {
        modulationWaveform(pulse_duty_cycle, pulse_rise_time, pulse_wave_type);
        pulseMode1(pulse_wave_type);
      } else if (sweep == 1) {
        createSweepWave(sweep_start_freq, sweep_end_freq, sweep_time);
      } else if (random_freq_jump == 1) {
        createRandomFreqWave(carrier_freq, random_freq_jump_max, random_freq_cycles);
      } else if (random_amp_jump == 1) {
        createRandomAmpWave(carrier_amp, random_amp_jump_max, random_amp_cycles);
      } else if (num_of_bounds > 0) {
        createWeightedFreqWave(num_of_bounds, weighted_lower_bounds, weighted_upper_bounds, weighted_amounts, weighted_freq_cycles);
      } else {
        channel1_freq = carrier_freq;
        pSine1->frequency(carrier_freq);
        rampOutput(carrier_amp, 3, 50, 0);
      }
    } else {
      resetValues();
    }
  }

}
