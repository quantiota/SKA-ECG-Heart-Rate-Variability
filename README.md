# SKA Heart Rate Variability

**Heart Rate Variability (HRV) Exploration with Structured Knowledge Accumulation (SKA) and Entropy-Based Learning**

This project applies the SKA entropy learning framework to heart rate variability (HRV) time series, aiming to discover new informational regimes and subtle physiological patterns not accessible with classical statistics or supervised machine learning.



## Features

- Real-time HRV analysis using entropy-driven SKA learning
- Extraction of regime transitions and entropy trajectories
- Visualization tools for HRV time series, entropy, and state transitions
- Open-source sample code, datasets, and reproducible figures



## Quick Start

1. Clone this repo  
   `git clone https://github.com/quantiota/SKA-Heart-Rate-Variability.git`
2. Install requirements  
   `pip install -r requirements.txt`
3. Run analysis notebook or script (see `notebooks/` or `scripts/`)



## Example Figures

> _Add here a key HRV entropy trajectory or regime plot demonstrating unique SKA insights._



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
ECG / HRV signal
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
- **Real-time, beat-by-beat entropy computation**
- **Detection of hidden regime cycling** and subtle state transitions
- **Open-source, reproducible code and methodology**

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