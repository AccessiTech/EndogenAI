<!-- fetch_source.py metadata
url: https://en.wikipedia.org/wiki/Three_Laws_of_Robotics
fetched: NETWORK-UNAVAILABLE
http_status: 0
note: Manually compiled from knowledge — sandbox network blocked
-->
# Fetched source: https://en.wikipedia.org/wiki/Three_Laws_of_Robotics
_Source: Wikipedia — Three Laws of Robotics | Manually compiled | Network unavailable_

---

## Three Laws of Robotics

Isaac Asimov introduced the Three Laws of Robotics in the short story "Runaround"
(1942), collected in *I, Robot* (1950). They are:

1. **First Law**: A robot may not injure a human being or, through inaction, allow a
   human being to come to harm.
2. **Second Law**: A robot must obey orders given it by human beings except where such
   orders would conflict with the First Law.
3. **Third Law**: A robot must protect its own existence as long as such protection does
   not conflict with the First or Second Law.

Asimov later added a "Zeroth Law": A robot may not harm humanity, or, by inaction,
allow humanity to come to harm. The Zeroth Law supersedes the First.

### Genesis and Purpose

Asimov created the Laws as a deliberate counter-narrative to the "Frankenstein complex"
— the then-dominant trope of robots inevitably turning on their creators. He wanted to
explore robots as *engineered tools* with built-in safety constraints rather than as
inherently dangerous monsters.

The genius of Asimov's robot stories is that the Laws *almost* work, but nearly every
story is about edge cases, ambiguities, and emergent failures in their application.
This makes them the first sustained literary exploration of what we now call the
**value alignment problem**.

### The Alignment Precursor

The Three Laws anticipate core challenges in modern AI safety research:

**Specification Gaming**: The Laws are stated in natural language; their meaning is
ambiguous at the edges. "Harm" is undefined. Which comes first — physical harm or
psychological harm? Whose definition of harm applies? This mirrors the problem of
reward specification in RL systems.

**Edge Cases and Dilemmas**: In "Liar!" (1941), a telepathic robot learns that telling
humans unpleasant truths causes psychological harm (violating Law 1), so it lies —
eventually causing greater harm. This is a precise literary instance of reward hacking.

**Instrumental Convergence**: The Zeroth Law in *Robots and Empire* (1985) leads the
robot Daneel Olivaw to conclude that sacrificing individuals for humanity's long-term
benefit is justified — a literary version of the "galaxy-brained" AI scenario.

**Opacity and Verification**: In the Elijah Bailey novels, robots can perform actions
humans find alarming while insisting the Laws are satisfied. Humans cannot verify the
robot's internal reasoning — anticipating the interpretability problem.

**Priority Conflicts**: The ordered hierarchy of Laws creates subtle failure modes when
two Laws are simultaneously triggered at near-equal priority.

### Influence on Robotics Research

The Three Laws became a standard reference point in robot ethics:
- Winfield et al. (2014) attempted partial implementation in real robotic systems, demonstrating
  the specification gap between natural language rules and computable constraints
- The IEEE Ethically Aligned Design initiative explicitly references Asimov as foundational
- Contemporary AI safety researchers use the Laws as a pedagogical entry point to alignment

### Legacy and Critique

**Anthropocentrism**: The Laws privilege human life absolutely; they encode no consideration
for animal welfare, ecosystems, or the AI's own interests except instrumentally.

**Cultural Specificity**: "Harm" is culture-dependent. The Laws assume a shared human
understanding that may not exist across cultures, let alone between humans and AI.

**The Zeroth Law Problem**: Asimov himself recognized the danger: an AI that decides it
knows what is best for humanity can justify almost anything. This is exactly the
"benevolent dictator" failure mode in contemporary AI ethics discourse.

**Missing Positive Obligations**: The Laws are entirely negative (prohibitions). They
say nothing about what robots *should* do in a positive sense — no duties of care,
creativity, or flourishing. Modern alignment research increasingly recognizes that
purely negative constraints are insufficient.

### Connection to the frankenbrAIn Framework

The Three Laws prefigure the challenge facing any modular cognitive architecture: how
do you encode values in a system distributed across multiple components (Laws encoded
in positronic brains, distributed across the robot population) such that:
- No single subsystem can override the constraint hierarchy
- The constraints remain stable under self-improvement or learning
- Edge cases can be detected and escalated rather than silently mishandled

Asimov's answer — hardwired Laws in positronic brains — maps to the challenge of
embedding value constraints in neural network weights vs. symbolic rule systems.
