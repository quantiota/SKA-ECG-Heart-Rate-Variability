# SKA Heart Rate Variability

 [![arXiv](https://img.shields.io/badge/arXiv-2503.13942-b31b1b)](https://arxiv.org/abs/2503.13942)   [![arXiv](https://img.shields.io/badge/arXiv-2504.03214-b31b1b)](https://arxiv.org/abs/2504.03214)   [![Hugging Face](https://img.shields.io/badge/🤗%20Hugging%20Face-SKA-orange)](https://huggingface.co/quant-iota) [![Sponsor](https://img.shields.io/badge/Sponsor-quantiota-ea4aaa?logo=github-sponsors)](https://github.com/sponsors/quantiota)


**Heart Rate Variability (HRV) Exploration with Structured Knowledge Accumulation (SKA) and Entropy-Based Learning**

This project applies the SKA entropy learning framework to the raw ECG waveform, streamed in real time, and to the heart rate variability (HRV) it carries — aiming to register informational regimes and subtle physiological patterns not accessible with classical statistics or supervised machine learning.



## Status

Early stage. The acquisition stream is in place: [`bitalino-stream/`](bitalino-stream/) reads the
raw ECG waveform from a BITalino board at 1000 Hz and writes it, sample by sample, into QuestDB
for the SKA real-time learner. Results, figures and the sequence library will be added as runs
are collected.

The SKA real-time engine is proprietary and is not included in this repository.



## Quick Start

```bash
git clone https://github.com/quantiota/SKA-ECG-Heart-Rate-Variability.git
cd SKA-ECG-Heart-Rate-Variability/bitalino-stream
pip install -r requirements.txt

# test without hardware
python ska_stream.py --simulate --seconds 5 --dry-run

# live ECG from the board (USB) into QuestDB
python ska_stream.py --port /dev/ttyUSB0
```

See [`bitalino-stream/README.md`](bitalino-stream/README.md) for setup, safety notes and the table layout.



## Why the raw waveform

Classical HRV reduces the ECG to beat-to-beat (RR) intervals. Here the learner reads the **raw
waveform at 1000 Hz**: the sample index is a constant 1 ms clock, every beat is read in full
(P wave, QRS complex, T wave), and the rhythm appears in the spacing between beats rather than
being extracted beforehand.



## Why SKA for HRV?

- **Unsupervised regime change detection** in HRV
- **Quantifies entropy** even during stable heart rate segments
- **Reveals subtle physiological transitions** invisible to classical HRV analysis

## Relation to SKA Quantitative Finance

This repository is part of a broader SKA research program on entropy-driven regime transitions in real-time dynamical systems.

The first empirical discovery of a SKA binary information flow was obtained in the quantitative finance repository:


[SKA-quantitative-finance](https://github.com/quantiota/SKA-quantitative-finance/tree/main/ska_engine_c/binary_transition_space)


In that work, market microstructure is encoded through three entropy regimes:

```
neutral = 00
bull    = 01
bear    = 10
```
and each transition becomes a 4-bit word:

```
neutral → neutral = 0000
neutral → bull    = 0001
neutral → bear    = 0010
bull → neutral    = 0100
bear → neutral    = 1000
```
The central hypothesis of SKA-HRV is that physiological signals may also express hidden health-related structure through entropy-regime sequences.

In this sense, SKA-HRV investigates whether the heart, like the market, produces a measurable binary information flow — not as a metaphor, but as a real sequence structure derived from entropy learning.

We hypothesize that the heart may “speak” a hidden informational language reflecting its physiological state and adaptive health. Under this framework, healthy and pathological conditions may correspond not only to changes in classical HRV metrics, but also to differences in entropy-regime grammar, transition diversity, and sequence organization.



## Pathology Sequence Library

Unlike classical supervised machine learning approaches, SKA-HRV does not rely primarily on training large black-box models.

Instead, the framework aims to build a **library of physiological entropy-regime sequences** derived directly from real-time ECG dynamics.

The proposed pipeline is:

```
raw ECG waveform (1000 Hz)
        ↓
SKA entropy computation
        ↓
neutral / bull / bear regimes
        ↓
4-bit transition words
        ↓
binary information flow
        ↓
sequence-pattern mapping
```

Under this framework, healthy and pathological cardiac states may correspond to distinct binary transition grammars and entropy-regime organizations.

Examples of future mapped conditions may include:

Healthy autonomic regulation
Stress and fatigue states
Recovery dynamics
Arrhythmia-related instability
Autonomic dysfunction
Sleep-related physiological transitions

The long-term objective is to create an open and extensible SKA Pathology Sequence Library, where physiological conditions are associated with characteristic entropy-transition structures rather than only statistical HRV metrics.

In this sense, SKA-HRV investigates whether cardiac physiology can be interpreted as a measurable informational language emerging from real-time entropy dynamics.


## Collaboration & Citation

### 👥 **Collaboration Call: HRV + Machine Learning Researchers**

We seek collaboration with **established HRV researchers who have published in HRV analysis and machine learning** to explore SKA's entropy-based regime discovery in physiological time series.

#### What We Bring:
- **Novel SKA entropy framework:** Proven in market regime detection, now applied to HRV
- **Real-time, sample-by-sample entropy computation on the raw ECG**
- **Detection of hidden regime cycling** and subtle state transitions
- **Open-source acquisition stream and exported data**

#### Ideal Collaborator:
- **Published HRV researchers** with clinical/medical datasets
- **Machine learning expertise** in time series or physiological signal processing
- **Interest in information-theoretic approaches** to biosignals
- **Willing to co-author research papers/validation studies**

#### Example Collaboration Areas:
- Clinical validation on cardiac datasets (ICU, ambulatory, sleep, etc.)
- Comparison of SKA vs. traditional HRV metrics (RMSSD, pNN50, SDNN, etc.)
- Applications in real-time monitoring: sports, critical care, neurocardiology
- Methodology papers: Information theory meets physiology


#### Citation

If you use or extend this project, please cite:  

* Bouarfa Mahi.
  Structured Knowledge Accumulation: An Autonomous Framework for Layer-Wise Entropy Reduction in Neural Learning
  [arXiv:2503.13942](https://arxiv.org/abs/2503.13942)
* Bouarfa Mahi.
  Structured Knowledge Accumulation: The Principle of Entropic Least Action in Forward-Only Neural Learning
  [arXiv:2504.03214](https://arxiv.org/abs/2504.03214)


**Contact:** Bouarfa Mahi — _especially interested in collaboration with those having access to large HRV datasets or clinical validation environments._



## License

MIT



*SKA-HRV-Analysis bridges the gap between modern information theory and physiological data science*