---
id: brain-structure
version: 0.1.0
status: in-progress
authority: descriptive
last-reviewed: 2026-02-23
seed-collection: brain.long-term-memory
chunking: section-boundary
maps-to-modules:
  - modules/group-i-signal-processing/sensory-input
  - modules/group-i-signal-processing/attention-filtering
  - modules/group-i-signal-processing/perception
  - modules/group-ii-cognitive-processing/memory/working-memory
  - modules/group-ii-cognitive-processing/memory/short-term-memory
  - modules/group-ii-cognitive-processing/memory/long-term-memory
  - modules/group-ii-cognitive-processing/memory/episodic-memory
  - modules/group-ii-cognitive-processing/affective
  - modules/group-ii-cognitive-processing/reasoning
  - modules/group-iii-executive-output/executive-agent
  - modules/group-iii-executive-output/agent-runtime
  - modules/group-iii-executive-output/motor-output
  - modules/group-iv-adaptive-systems/learning-adaptation
  - modules/group-iv-adaptive-systems/metacognition
---

# Brain Structure

An overview of the human brain's structure, including its major regions and their functions. This document is the
**authoritative descriptive reference** for neuromorphic analogies across the brAIn framework — each region's function,
connectivity, and characteristics inform the design of the corresponding cognitive module.

> Each major region section follows a consistent structure where applicable:
>
> - **Module analogy** — which brAIn module(s) this region maps to
> - **Function** — primary cognitive/biological role
> - **Inputs from** — upstream regions
> - **Outputs to** — downstream regions
> - **Key design notes** — implications for module design

## Outline

An extensive outline of the human brain's structure, including major regions, subregions, and their known functions.
This can serve as a reference for understanding how different parts of the brain contribute to various cognitive and
behavioral functions.

1. **Cerebrum** — largest part of the brain; divided into left and right hemispheres connected by the corpus callosum

   1. **Cerebral Cortex** — outer grey matter layer, 2–4 mm thick, deeply folded (gyri and sulci)
      1. **Neocortex** — six neuronal layers; mapped into ~50 Brodmann areas
      2. **Allocortex** — three or four layers; includes paleocortex and archicortex
      3. **Motor Cortex** — planning and coordinating voluntary movement
         1. Primary Motor Cortex (precentral gyrus) — executes voluntary movement; body mapped as motor homunculus
         2. Premotor Area — supports and prepares primary motor cortex
         3. Supplementary Motor Area — coordinates complex, bilateral movements
      4. **Sensory Cortex** — receives and processes sensory input
         1. Somatosensory Cortex (postcentral gyrus, parietal lobe) — touch, pressure, pain, vibration, temperature,
            proprioception
         2. Visual Cortex (occipital lobe) — processes visual input from the retinas
         3. Auditory Cortex (temporal lobe / insular cortex) — processes sound
         4. Gustatory Cortex — processes taste signals relayed via thalamus
         5. Olfactory Cortex — processes smell via olfactory bulb
      5. **Association Areas** — integrate sensory and motor information; involved in perception, thought, and
         decision-making
   2. **Frontal Lobe** — reasoning, motor control, emotion, language, planning, attention, self-control
      1. Prefrontal Cortex — higher-order cognition, working memory, executive functions, personality
         1. Dorsolateral Prefrontal Cortex (DLPFC) — planning, working memory manipulation
         2. Orbitofrontal Cortex — emotion generation, reward evaluation
         3. Anterior Cingulate Cortex — planning, error detection, attentional control
      2. Primary Motor Cortex — voluntary movement execution
      3. Broca's Area (left hemisphere) — language production and speech
   3. **Parietal Lobe** — sensory integration; spatial awareness; attention
      1. Somatosensory Cortex — body sensation (touch, position, pain)
      2. Supramarginal Gyrus — language and spatial processing
   4. **Temporal Lobe** — auditory and visual memory, language comprehension, hearing, speech
      1. Auditory Cortex — sound processing
      2. Wernicke's Area (left hemisphere) — language comprehension
      3. Hippocampus — memory formation and spatial navigation (paired; part of limbic system)
      4. Amygdala — emotional processing, especially fear; threat detection (paired; part of limbic system)
   5. **Occipital Lobe** — visual reception, spatial processing, movement perception, colour recognition
      1. Visual Cortex — receives and processes retinal signals
      2. Cuneus — visual processing lobule within occipital lobe
   6. **Insular Lobe (Insular Cortex)** — interoception, pain, emotion, taste, autonomic regulation
   7. **Limbic Lobe** — emotion, motivation, memory
      1. Hippocampus — declarative memory, spatial navigation
      2. Amygdala — emotion (fear, reward), emotional memory
      3. Cingulate Cortex — emotion regulation, learning, memory
   8. **Basal Ganglia** — behaviour and movement regulation, habit formation, reward
      1. Striatum
         1. Caudate Nucleus — voluntary movement, learning, memory
         2. Putamen — movement regulation, procedural learning
         3. Nucleus Accumbens (ventral striatum) — reward, motivation, reinforcement
         4. Olfactory Tubercle (ventral striatum) — olfactory processing, reward
      2. Globus Pallidus — modulates voluntary movement via inhibitory output
      3. Substantia Nigra — dopamine production; motor control and reward
      4. Subthalamic Nucleus — movement modulation; inhibitory control
      5. Claustrum — thin neuronal sheet at lateral sulcus; speculated role in consciousness / sensory integration
   9. **Basal Forebrain** — major cholinergic output to neocortex and striatum
      1. Nucleus Basalis (of Meynert) — cholinergic neurons; memory and attention
      2. Diagonal Band of Broca — acetylcholine production; memory
      3. Medial Septal Nucleus — hippocampal modulation
      4. Substantia Innominata — arousal and memory consolidation
   10. **Diencephalon** — deep forebrain structures beneath the cortex
       1. **Thalamus** — relay hub for all sensory signals (except smell) to the cortex; regulates consciousness and
          alertness
       2. **Hypothalamus** — homeostasis, circadian rhythm, autonomic control, endocrine regulation, thermoregulation,
          hunger, thirst
          1. Suprachiasmatic Nucleus — circadian clock generator
          2. Ventrolateral Preoptic Nucleus — sleep regulation
          3. Lateral Hypothalamus — appetite and arousal via orexin neurons
       3. **Epithalamus** — emotion and environmental cue regulation
          1. Pineal Gland — melatonin secretion; circadian regulation
       4. **Subthalamus** — movement coordination
       5. **Pituitary Gland** — master endocrine gland; controlled by hypothalamus via oxytocin, vasopressin, dopamine
   11. **Ventricular System** — CSF production and circulation
       1. Two Lateral Ventricles — within each cerebral hemisphere
       2. Third Ventricle — midline; connected to lateral ventricles via interventricular foramina
       3. Fourth Ventricle — between pons/cerebellum; drains CSF via apertures to subarachnoid space
       4. Cerebral Aqueduct — connects third and fourth ventricles

2. **Cerebellum** — "little brain"; movement coordination, balance, posture, fine motor precision

   1. Anterior Lobe — motor movement coordination and smoothing
   2. Posterior Lobe — motor coordination; likely role in cognition and behaviour
   3. Flocculonodular Lobe — balance and equilibrium
   4. Cerebellar Vermis — connects anterior and posterior lobes at midline
   5. Cerebellar Peduncles — three pairs of nerve tracts connecting cerebellum to brainstem
      1. Superior — connects to midbrain
      2. Middle — connects to medulla
      3. Inferior — connects to pons

3. **Brainstem** — connects cerebrum to spinal cord; regulates vital autonomic functions; conduit for nerve tracts

   1. **Midbrain (Mesencephalon)** — visual and auditory reflexes, eye movement, motor control
      1. Substantia Nigra (midbrain portion) — dopaminergic; movement and reward
      2. Reticular Formation — consciousness, attention, arousal (runs through brainstem)
   2. **Pons** — breathing regulation, sleep, facial sensation and movement
      1. Pneumotaxic Centre — controls breath duration
      2. Apneustic Centre — influences inhalation
   3. **Medulla Oblongata** — vital autonomic regulation
      1. Vasomotor Centre — blood pressure and heart rate control via sympathetic/parasympathetic systems
      2. Dorsal Respiratory Group — drives inhalation; receives body sensory input
      3. Ventral Respiratory Group — exhalation regulation during exertion
      4. Solitary Nucleus — receives taste and visceral sensory input
      5. Medullary Pyramids — decussation point for corticospinal tract (motor fibres cross sides here)

4. **Meninges** — three protective membranes surrounding the brain and spinal cord

   1. Dura Mater — tough outer membrane
   2. Arachnoid Mater — middle membrane; subarachnoid space beneath contains CSF
   3. Pia Mater — delicate inner membrane; closely follows brain surface
   4. Subarachnoid Lymphatic-like Membrane (SLYM) — proposed fourth membrane (2023)

5. **Cerebrospinal Fluid (CSF)** — clear fluid cushioning the brain; waste clearance via glymphatic system; circulates
   through ventricles and subarachnoid space

6. **Blood Supply**
   1. Internal Carotid Arteries — supply anterior brain via anterior and middle cerebral arteries
   2. Vertebral Arteries — supply posterior brain; join to form basilar artery
   3. Circle of Willis — arterial ring connecting both circulations at the base of the brain
   4. Blood–Brain Barrier — tight-junction capillary lining protecting brain from bloodstream substances

## Brain Region to Agent / Skill / Prompt / Resource Mapping

A table mapping brain regions to potential agent functions, skills, prompts, or resources that could be inspired by the
known functions of those brain regions. This is a speculative mapping and can be expanded with more detailed functions
and interactions.
