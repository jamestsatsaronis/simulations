# Biochemistry simulations

A collection of interactive teaching tools for biochemistry and molecular biology students. Each tool is a single, self-contained HTML file, published at https://jamestsatsaronis.github.io/simulations/. There's no build step, framework or install. Open a file in a browser to use it.

The tools are designed to be hosted on GitHub Pages and embedded in a learning management system (LMS) through an `<iframe>`.

## Contents

### Amino acids and proteins
| File | What it does |
|---|---|
| [`amino-acid-code-drill.html`](https://jamestsatsaronis.github.io/simulations/amino-acid-code-drill.html) | Practice matching amino acid names with their three-letter and one-letter codes. |
| [`amino-acid-tags.html`](https://jamestsatsaronis.github.io/simulations/amino-acid-tags.html) | Classify amino acid side chains (for example polar, charged, hydrophobic). |
| [`charge-at-pH.html`](https://jamestsatsaronis.github.io/simulations/charge-at-pH.html) | Practice working out the net charge of amino acids and peptides at a given pH. |
| [`ramachandran-explorer.html`](https://jamestsatsaronis.github.io/simulations/ramachandran-explorer.html) | Explore phi/psi backbone angles on a Ramachandran plot, with 3D views (uses 3Dmol.js). |
| [`secondary-structure-views.html`](https://jamestsatsaronis.github.io/simulations/secondary-structure-views.html) | Interactive 3D views of protein secondary structure. |

### Purification and chromatography
| File | What it does |
|---|---|
| [`ion-exchange-chromatography.html`](https://jamestsatsaronis.github.io/simulations/ion-exchange-chromatography.html) | Interactive ion exchange chromatography activity. |
| [`protein-purification-tool.html`](https://jamestsatsaronis.github.io/simulations/protein-purification-tool.html) | A tutorial activity on protein purification. |
| [`protein-purification-lab-interleaved.html`](https://jamestsatsaronis.github.io/simulations/protein-purification-lab-interleaved.html) | A virtual purification lab where the steps are interleaved with visual gels. |

### Enzymes and molecular techniques
| File | What it does |
|---|---|
| [`enzyme-kinetics-sim.html`](https://jamestsatsaronis.github.io/simulations/enzyme-kinetics-sim.html) | Michaelis-Menten enzyme kinetics. |
| [`reaction-coordinate-builder.html`](https://jamestsatsaronis.github.io/simulations/reaction-coordinate-builder.html) | Build reaction coordinate (energy profile) diagrams. |
| [`qrtpcr-simulation_5.html`](https://jamestsatsaronis.github.io/simulations/qrtpcr-simulation_5.html) | A qRT-PCR simulation using a SYBR Green assay. |

## Using them

- **Locally:** open any `.html` file in a modern browser.
- **Online:** every tool is published with GitHub Pages at `https://jamestsatsaronis.github.io/simulations/<file>.html`. The links in the tables above open the live versions. The landing page at the site root (`index.html`) lists them all.
- **In an LMS:** embed the hosted URL with an iframe, for example:
  ```html
  <iframe src="https://jamestsatsaronis.github.io/simulations/enzyme-kinetics-sim.html"
          width="100%" height="700" title="Enzyme kinetics"></iframe>
  ```

## Technical notes

- Plain HTML, CSS and JavaScript in one file per tool, with no local dependencies.
- Most tools load the Public Sans font from Google Fonts. The 3D tool `ramachandran-explorer.html` also loads [3Dmol.js](https://3dmol.org) from its CDN. These need an internet connection, although the pages fall back to system fonts if the fonts don't load.
- Most pages include a [GoatCounter](https://www.goatcounter.com) script for privacy-friendly usage counts. Remove that `<script>` tag if you fork the repository and don't want it.
- The tools aim for a calm, consistent look and accessible design (WCAG 2.2 AA).

## Contributing

To add a tool, put a new self-contained `.html` file in the repository root and add it to the tables above.
