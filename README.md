# Biochemistry simulations

A collection of interactive teaching tools for biochemistry and molecular biology students. Each tool is a single, self-contained HTML file. There's no build step, framework or install. Open a file in a browser to use it.

The tools are designed to be hosted on GitHub Pages and embedded in a learning management system (LMS) through an `<iframe>`.

## Contents

### Amino acids and proteins
| File | What it does |
|---|---|
| `amino-acid-code-drill.html` | Practice matching amino acid names with their three-letter and one-letter codes. |
| `amino-acid-tags.html` | Classify amino acid side chains (for example polar, charged, hydrophobic). |
| `amino-acid-ph-sim.html` | Watch amino acid protonation states change as pH moves. |
| `charge-at-pH.html` | Practice working out the net charge of amino acids and peptides at a given pH. |
| `amino-blaster.html` | An arcade-style game for reinforcing amino acid knowledge. |
| `ramachandran-explorer.html` | Explore phi/psi backbone angles on a Ramachandran plot, with 3D views (uses 3Dmol.js). |
| `secondary-structure-views.html` | Interactive 3D views of protein secondary structure. |

### Purification and chromatography
| File | What it does |
|---|---|
| `ion-exchange-animation.html` | Animation of how ion exchange chromatography separates proteins. |
| `ion-exchange-chromatography.html` | Interactive ion exchange chromatography activity. |
| `protein-purification-tool.html` | A tutorial activity on protein purification. |
| `protein-purification-lab-interleaved.html` | A virtual purification lab where the steps are interleaved with visual gels. |

### Enzymes and molecular techniques
| File | What it does |
|---|---|
| `enzyme-kinetics-sim.html` | Michaelis-Menten enzyme kinetics. |
| `reaction-coordinate-builder.html` | Build reaction coordinate (energy profile) diagrams. |
| `qrtpcr-simulation_5.html` | A qRT-PCR simulation using a SYBR Green assay. |

## Using them

- **Locally:** open any `.html` file in a modern browser.
- **Online:** enable GitHub Pages for the repository. Each file is then available at `https://<user>.github.io/simulations/<file>.html`.
- **In an LMS:** embed the hosted URL with an iframe, for example:
  ```html
  <iframe src="https://<user>.github.io/simulations/enzyme-kinetics-sim.html"
          width="100%" height="700" title="Enzyme kinetics"></iframe>
  ```

## Technical notes

- Plain HTML, CSS and JavaScript in one file per tool, with no local dependencies.
- Most tools load the Public Sans font from Google Fonts. The 3D tool `ramachandran-explorer.html` also loads [3Dmol.js](https://3dmol.org) from its CDN. These need an internet connection, although the pages fall back to system fonts if the fonts don't load.
- Most pages include a [GoatCounter](https://www.goatcounter.com) script for privacy-friendly usage counts. Remove that `<script>` tag if you fork the repository and don't want it.
- The tools aim for a calm, consistent look and accessible design (WCAG 2.2 AA).

## Contributing

To add a tool, put a new self-contained `.html` file in the repository root and add it to the tables above.
