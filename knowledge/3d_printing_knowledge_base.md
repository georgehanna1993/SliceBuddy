3D Printing Knowledge Base (FDM – Practical Rules)

Materials Overview

PLA
	•	Easiest material to print
	•	Minimal warping
	•	Brittle under mechanical stress
	•	Low heat resistance (~60°C)
	•	Best for decorative models and prototypes
	•	High cooling fan recommended

PETG
	•	Stronger and tougher than PLA
	•	Better layer adhesion
	•	Slightly flexible
	•	More prone to stringing
	•	Better temperature resistance (~75°C)
	•	Ideal for functional parts like brackets and holders
	•	Use moderate cooling (less than PLA)

ABS
	•	Strong and impact resistant
	•	High heat resistance (~95°C)
	•	Warps easily without enclosure
	•	Produces fumes
	•	Recommended for mechanical parts
	•	Enclosure strongly recommended

ASA
	•	Similar to ABS
	•	UV resistant
	•	Good for outdoor use
	•	Warping risk without enclosure

TPU
	•	Flexible material
	•	Print slowly
	•	Avoid aggressive retraction
	•	Difficult supports removal
	•	Ideal for flexible parts (gaskets, cases)

⸻

Orientation Rules
	•	Maximize bed contact area
	•	Avoid tall, narrow prints when possible
	•	Layers are weakest in Z direction
	•	For mechanical strength, align stress parallel to layers
	•	Reorient to reduce support use

⸻

Supports and Overhangs
	•	Most printers handle up to 45° overhang
	•	Bridges under 20mm often printable without supports
	•	Large flat overhangs require supports
	•	Tree supports reduce scarring on figurines
	•	Consider splitting model instead of heavy supports

⸻

Bed Adhesion

Use brim when:
	•	Model footprint is small
	•	Print is tall
	•	Printing ABS or ASA

Adhesion tips:
	•	Clean bed with IPA
	•	Proper first layer squish
	•	Slow first layer speed
	•	Correct bed temperature

⸻

Tall Print Stability

Tall prints may:
	•	Wobble
	•	Shift layers
	•	Detach from bed

Mitigation:
	•	Use brim (5–10mm)
	•	Increase wall count
	•	Reduce print speed
	•	Ensure tight belts and stable frame

⸻

Infill Guidelines
	•	Decorative prints: 10–15%
	•	Functional prints: 20–40%
	•	Mechanical load: 40%+
	•	Increasing walls often improves strength more than infill

⸻

Wall Count Guidelines
	•	2 walls: light decorative parts
	•	3 walls: general prints
	•	4+ walls: functional parts
	•	Tall prints benefit from increased walls

⸻

Warping Causes
	•	Uneven cooling
	•	Drafts
	•	No enclosure (ABS/ASA)

Mitigation:
	•	Enclosure
	•	Brim
	•	Stable ambient temperature

⸻

Stringing Causes (PETG / TPU)
	•	High temperature
	•	Wet filament
	•	Excessive retraction

Fix:
	•	Slightly reduce temperature
	•	Dry filament
	•	Tune retraction carefully

⸻

First Layer Best Practices
	•	Slight squish
	•	Slow speed
	•	Clean bed
	•	Correct Z offset

⸻

Use-Case Questions Before Recommending Settings
	•	Where will the part be used: indoors, outdoors, sunlight, inside a car, or near an engine?
	•	Is the goal decorative appearance, general use, mechanical strength, or flexibility?
	•	Will the part hold weight or experience repeated force?
	•	Is failure merely inconvenient, or could failure cause injury or property damage?
	•	STL files are unitless. Confirm millimeters if dimensions look unexpected.
	•	3MF files declare units. Convert those dimensions to millimeters before recommending settings.

⸻

Environment Guidance

Indoor decorative parts
	•	PLA is usually the easiest starting point
	•	Focus on appearance and clean surfaces
	•	Moderate infill is usually sufficient

Outdoor or sunlight exposure
	•	ASA is preferred for UV and weather resistance
	•	PETG can be an alternative for less demanding exposure
	•	Consider drainage and water traps in the model

Inside a car
	•	Vehicle interiors can become hot in sunlight
	•	PLA can soften in elevated temperatures
	•	ASA is a more conservative starting recommendation
	•	Test fit and performance under realistic heat exposure

Car parts, engine areas, and safety-critical parts
	•	A print plan is not a safety certification
	•	Heat, vibration, load cycles, chemicals, and failure consequences matter
	•	Use engineering review and physical testing before relying on a printed part
	•	Do not rely on a hobby FDM print for safety-critical use without validation

⸻

Load Guidance
	•	No meaningful load: optimize for print quality and ease
	•	Light load: use at least general-purpose wall settings
	•	Regular functional load: increase walls and infill; PETG is often a practical starting point
	•	High load: increase walls and infill, analyze load direction, and physically test the part
	•	Layer orientation matters because FDM parts are weakest between layers

⸻

Reliability Boundaries
	•	Geometry analysis can detect mesh health, dimensions, contact area, and overhang signals
	•	Geometry analysis cannot infer real-world load direction, printer calibration, filament quality, or required safety factor
	•	User context and printer profile data are needed for a more reliable recommendation
	•	Always test critical prints under realistic conditions

⸻

Speed Guidance
	•	Speed values are conservative starting points, not guarantees.
	•	Use slower first layers for adhesion.
	•	Reduce print and outer-wall speed for tall models to limit wobble.
	•	Print TPU slowly and avoid aggressive retraction.
	•	Use the filament manufacturer's printer profile for exact temperatures.
