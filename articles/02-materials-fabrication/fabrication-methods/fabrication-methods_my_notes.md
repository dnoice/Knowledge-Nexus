<!--
✒ Metadata
    - Title: My Notes - Fabrication Methods (Materials Fabrication - v1.0)
    - File Name: fabrication-methods_my_notes.md
    - Relative Path: core\02-materials-fabrication\fabrication-methods\fabrication-methods_my_notes.md
    - Artifact Type: docs
    - Version: 1.0.0
    - Date: 2026-01-02
    - Update: Thursday, January 02, 2026
    - Author: Dennis 'dnoice' Smaltz
    - A.I. Acknowledgement: Google Deep Mind - Gemini 3 Pro
    - Signature: ︻デ═─── ✦ ✦ ✦ | Aim Twice, Shoot Once!

✒ Description:
    Personal study notes and key takeaways from fabrication methods research.
    Distilled insights, memorable concepts, and areas for deeper exploration.
    Focused purely on the science of fabrication—no tangential connections.

✒ Key Features:
    - Feature 1: Distilled key concepts and mental models
    - Feature 2: Important numbers and threshold values
    - Feature 3: Process selection decision frameworks
    - Feature 4: Common pitfalls and failure modes
    - Feature 5: Areas warranting deeper study
    - Feature 6: Terminology quick reference

✒ Usage Instructions:
    Personal reference for quick recall of fabrication fundamentals.
    Use for review and as a springboard for further research.

✒ Other Important Information:
    - Dependencies: None (documentation only)
    - Related documents: fabrication-methods.md, fabrication-methods_works_cited.md
    - Note: Subject-focused only—no cross-project connections
---------
-->

# My Notes: The Science Behind Fabrication Methods

## Core Mental Model

The processing-structure-property paradigm is the backbone of materials fabrication science. Every decision traces back to this chain:

```text
Process Parameters → Microstructure → Properties → Performance
```

You cannot shortcut this. If you want specific properties, you must control microstructure. If you want specific microstructure, you must control process parameters. Work backwards from desired outcome.

## The Four Pillars of Fabrication

1. **Additive** — Build up layer by layer
2. **Subtractive** — Remove material from larger block
3. **Formative** — Reshape without adding/removing mass
4. **Deposition** — Apply thin layers to substrates

Each pillar has its physics. Learn which mechanism dominates each process.

## Critical Temperature Thresholds

| Material Class | Recrystallization Range | Hot Working Above |
| -------------- | ----------------------- | ----------------- |
| Steel          | 600–900°C               | ~0.5–0.7 Tm       |
| Aluminum       | 200–300°C               | ~150–200°C        |
| Copper         | 300–400°C               | ~200°C            |

**Key insight**: Recrystallization temperature is THE dividing line between hot and cold working. Above it = simultaneous deformation and recrystallization. Below it = strain hardening accumulates.

The rule of thumb: Hot working temperature is typically 0.5–0.8 times the absolute melting point (Tm in Kelvin).

## Sintering — The Six Mass Transport Mechanisms

This was a revelation. Six different atomic pathways:

1. Surface diffusion (non-densifying)
2. Vapor transport (non-densifying)
3. Lattice diffusion from surface (non-densifying)
4. Lattice diffusion from grain boundary (DENSIFYING)
5. Grain boundary diffusion (DENSIFYING)
6. Plastic deformation (DENSIFYING)

Only mechanisms 4–6 actually shrink pores. Understanding which mechanism dominates tells you how to optimize.

**Practical implication**: Finer powders sinter faster because diffusion distances are shorter. A 14x reduction in particle size can give 1000x faster sintering rates.

## Solidification Microstructure Zones

When casting metals, expect three distinct zones:

1. **Chill zone** — Fine equiaxed grains at mold wall (rapid nucleation from thermal shock)
2. **Columnar zone** — Elongated grains growing inward along temperature gradient
3. **Central equiaxed zone** — If constitutional supercooling is sufficient

Cooling rate controls everything. Faster cooling = finer microstructure = generally better properties.

## Dendrites and Segregation

Dendritic growth is unavoidable in alloy solidification. The tree-like structures form because:

- Solute rejection at the solidification front creates composition gradients
- Perturbations in the interface amplify because tips grow faster than valleys
- Secondary and tertiary arms branch off primary stems

**Two types of segregation**:

- Microsegregation — Over distances comparable to dendrite arm spacing (can homogenize)
- Macrosegregation — Over distances comparable to casting size (cannot homogenize easily)

Microsegregation is fixable with heat treatment. Macrosegregation is permanent unless you remelt.

## Powder Bed Fusion Key Parameters

For SLS/SLM success, balance these:

- **Laser power** — Energy input per unit time
- **Scan speed** — How fast the laser traverses
- **Hatch spacing** — Distance between adjacent scan lines
- **Layer thickness** — Height of each powder layer

The energy density (J/mm³) is the unifying metric: Power / (Speed × Hatch × Layer).

Too low = insufficient melting = porosity. Too high = keyholing, spatter, residual stress.

**Cooling rates in AM**: Can exceed 10,000°C/s — orders of magnitude faster than casting. This produces non-equilibrium phases and fine microstructures but also residual stress.

## Machining Fundamentals

The shear angle determines chip formation. Everything else flows from this geometry.

**Specific cutting energy** (power to remove unit volume) depends on:

- Material hardness and strain hardening rate
- Cutting speed and feed rate
- Tool geometry (rake angle, clearance angle)

Heat distribution during cutting:

- ~75% goes into chip (good — chip carries heat away)
- ~15% goes into tool (bad — causes wear)
- ~10% goes into workpiece (bad — causes distortion)

## Thin Film Deposition Decision Tree

**Physical Vapor Deposition (PVD)**: Line-of-sight processes, good for metals

- Evaporation — Thermal energy vaporizes source
- Sputtering — Ion bombardment ejects atoms from target

**Chemical Vapor Deposition (CVD)**: Surface reactions from gas precursors

- Higher conformality than PVD
- Can coat complex geometries
- Requires higher temperatures

**Atomic Layer Deposition (ALD)**: Self-limiting surface reactions

- Atomic-level thickness control
- Excellent conformality on high-aspect-ratio features
- Slower than CVD but more precise

## Photolithography Resolution Limits

Resolution is wavelength-dependent. The trend:

| Generation       | Wavelength | Feature Size      |
| ---------------- | ---------- | ----------------- |
| UV               | 365 nm     | ~500 nm           |
| DUV (ArF)        | 193 nm     | ~65 nm            |
| EUV              | 13.5 nm    | <10 nm            |

**Multiple patterning** extends resolution beyond single-exposure limits by combining multiple lithography steps.

## Forging vs. Casting — Property Comparison

Forged parts generally outperform cast parts because:

- Closed porosity from mechanical working
- Refined grain structure
- Grain flow follows part contours (enhances directional strength)
- Elimination of dendritic structure

**Grain flow** is critical. A machined part from bar stock has grain flow cut across geometry. A forged part has grain flow conforming to geometry. The forged crankshaft example from research makes this clear.

## Liquid Phase Sintering — The 90% Rule

~90% of commercial sintered products use liquid phase sintering because it moves material hundreds of times faster than solid-state diffusion.

Three requirements:

1. Liquid must wet solid particles (low contact angle)
2. Solids must dissolve somewhat in liquid
3. Process must proceed through rearrangement → solution-precipitation → final densification

## Hot vs. Cold Working Trade-offs

| Factor               | Hot Working          | Cold Working            |
| -------------------- | -------------------- | ----------------------- |
| Flow stress          | 1/5 to 1/3 of cold   | High                    |
| Ductility            | >50% achievable      | Limited                 |
| Residual stress      | Minimal              | Present                 |
| Surface finish       | Poor (oxide scale)   | Excellent (Ra ≤ 1.6 μm) |
| Dimensional accuracy | IT12–IT14            | IT8–IT10                |
| Tool wear            | Severe               | Moderate                |

**Warm forming** exists as a compromise — better ductility than cold, better finish than hot.

## CVD Process Steps (Sequential)

1. Precursor transport to reaction chamber
2. Gas-phase transport to substrate surface
3. Adsorption onto surface
4. Surface reaction (heterogeneous)
5. Byproduct desorption
6. Byproduct transport away from surface

Rate-limiting step determines overall kinetics. At low temperatures, surface reaction limits. At high temperatures, mass transport limits.

## Defects to Watch For

### In Castings

- Shrinkage porosity (feeding issues)
- Gas porosity (dissolved gas in melt)
- Hot tears (cracking during solidification)
- Inclusions (oxides, slags)
- Segregation (composition variations)

### In Forgings

- Surface cracking (excessive deformation)
- Fold-over defects (material doubled on itself)
- Dead zones (undeformed regions)
- Grain coarsening (too hot, too slow)

### In Powder Metallurgy

- Residual porosity (insufficient sintering)
- Oxide inclusions (from powder surfaces)
- Density gradients (from die compaction)
- Excessive grain growth (oversintering)

### In Thin Films

- Pinholes (discontinuities in coverage)
- Columnar voids (shadowing effects in PVD)
- Stress-induced delamination
- Particle contamination

## Equations Worth Remembering

**Arrhenius relationship for diffusion**:

```text
D = D₀ × exp(-Q/RT)
```

Where D = diffusion coefficient, Q = activation energy, R = gas constant, T = temperature.

**Extrusion ratio**:

```text
R = A₀/Af
```

Initial area over final area. Higher R = more severe deformation.

**Rolling reduction**:

```text
r = (h₀ - hf)/h₀
```

Fractional change in thickness per pass.

## Areas for Deeper Study

1. **Phase field modeling** — Computational approach to simulating solidification microstructure. Computationally intensive but gives unprecedented insight into dendrite formation.

2. **ICME (Integrated Computational Materials Engineering)** — Connecting process simulation to location-specific property prediction. The future of casting design.

3. **Friction stir processing** — Solid-state technique gaining traction. No melting, refined microstructure, unique property combinations.

4. **Spark plasma sintering** — Rapid consolidation with pulsed DC current. Achieves fine microstructures impossible by conventional means.

5. **Two-step sintering** — Clever approach from ceramics being adopted for metals. Dense parts without grain coarsening.

## Quick Terminology Reference

| Term                         | Definition                                                        |
| ---------------------------- | ----------------------------------------------------------------- |
| Annealing                    | Heat treatment to soften material and relieve stresses            |
| Austenite                    | High-temperature FCC phase of steel                               |
| Constitutional supercooling  | Compositional undercooling ahead of solidification front          |
| Dendritic structure          | Tree-like solidification morphology in alloys                     |
| Ductility                    | Ability to deform plastically without fracture                    |
| Epitaxial growth             | Crystal growth maintaining orientation of substrate               |
| Flow stress                  | Instantaneous stress required to continue plastic deformation     |
| Green part                   | Compacted but unsintered powder metallurgy component              |
| Heat-affected zone (HAZ)     | Region altered by heat but not melted during welding              |
| Homogenization               | Heat treatment to reduce segregation through diffusion            |
| Kerf                         | Width of material removed by cutting                              |
| Martensite                   | Hard, diffusionless transformation product in steel               |
| Melt pool                    | Localized molten region in welding or AM                          |
| Microstructure               | Structure visible at microscopic scale (grains, phases, defects)  |
| Necking                      | Localized reduction in cross-section during tensile deformation   |
| Nucleation                   | Formation of new phase embryos                                    |
| Porosity                     | Volume fraction of voids in material                              |
| Quenching                    | Rapid cooling to achieve non-equilibrium microstructure           |
| Recrystallization            | Formation of new strain-free grains in deformed material          |
| Sintering                    | Particle bonding through diffusion without full melting           |
| Strain hardening             | Increase in flow stress with plastic deformation                  |
| Swarf                        | Chips and debris from machining operations                        |
| Yield strength               | Stress at onset of plastic deformation                            |

## Final Thoughts

The more I dig into fabrication science, the more I appreciate that every process is a conversation with thermodynamics and kinetics. You propose a geometry and property set; the physics responds with what's actually achievable.

The masters of this field understand not just the "what" but the "why" at every scale — from atomic diffusion to macroscopic heat flow. That's the level to aspire to.

---

> **︻デ═─── ✦ ✦ ✦ | Aim Twice, Shoot Once!**
