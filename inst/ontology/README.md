# biocViews Ontology

This directory contains the biocViews ontology in OBO (Open Biological and Biomedical Ontologies) format, converted from the original DOT (Graphviz) format.

## Overview

The biocViews ontology is a controlled vocabulary for categorizing Bioconductor packages. It provides a structured hierarchy of terms that describe:

- **Software**: Computational tools and analysis methods
- **AnnotationData**: Curated biological metadata and reference information
- **ExperimentData**: Example datasets and research data
- **Workflow**: Complete analysis pipelines and best practices

## Files

- **biocViewsVocab.obo** - The ontology in OBO format (500 terms, 500 relationships)
- **convert_dot_to_obo.py** - Python script to convert DOT format to OBO format
- **validate_obo.py** - Python validation script for OBO file
- **test_ontology.R** - R validation script for OBO file (requires R installation)
- **README.md** - This file

## OBO File Format

The OBO (Open Biological and Biomedical Ontologies) format is a standardized text-based format for representing ontologies. Each term in the ontology includes:

- **id**: Unique identifier (e.g., `BIOCVIEWS:0000001`)
- **name**: Human-readable term name (e.g., `RNASeq`)
- **def**: Definition of the term (when available)
- **is_a**: Parent term(s) indicating hierarchical relationships

### Example Term

```obo
[Term]
id: BIOCVIEWS:0000038
name: RNASeq
def: "Sequencing technology for analyzing RNA transcripts to study gene expression and transcriptome dynamics." []
is_a: BIOCVIEWS:0000033 ! Sequencing
```

## Ontology Structure

The ontology is organized as a directed acyclic graph (DAG) with a single root term:

```
BiocViews (root)
├── Software
│   ├── Technology
│   │   ├── Sequencing
│   │   │   ├── RNASeq
│   │   │   ├── ChIPSeq
│   │   │   └── ...
│   │   └── Microarray
│   ├── ResearchField
│   ├── BiologicalQuestion
│   ├── WorkflowStep
│   ├── StatisticalMethod
│   └── ...
├── AnnotationData
│   ├── Organism
│   ├── ChipManufacturer
│   ├── PackageType
│   └── ...
├── ExperimentData
│   ├── OrganismData
│   ├── TechnologyData
│   ├── DiseaseModel
│   └── ...
└── Workflow
    ├── BasicWorkflow
    ├── GeneExpressionWorkflow
    └── ...
```

**Statistics:**
- Total terms: 500
- Root terms: 1 (BiocViews)
- Leaf terms: 464
- Maximum depth: 4 levels
- Total relationships: 500

## Using the OBO File

### In R

```r
# Option 1: Using ontologyIndex package
library(ontologyIndex)
biocviews <- get_ontology("biocViewsVocab.obo")

# Get all descendants of a term
get_descendants(biocviews, "BIOCVIEWS:0000033")  # Sequencing

# Option 2: Parse manually
lines <- readLines("biocViewsVocab.obo")
# ... custom parsing code ...
```

### In Python

```python
# Option 1: Using pronto package
import pronto
ontology = pronto.Ontology("biocViewsVocab.obo")

# Access terms
for term in ontology.terms():
    print(term.id, term.name)

# Option 2: Parse manually
# See validate_obo.py for example parsing code
```

## Validation

### Using Python (Recommended)

The validation script checks:
- OBO file format and structure
- Required fields for all terms (id, name)
- Valid is_a relationship references
- Absence of cycles (DAG property)
- Summary statistics

```bash
cd inst/ontology
python3 validate_obo.py
```

**Expected output:**
```
Testing OBO file: biocViewsVocab.obo
==================================================
Parsing OBO file...
  ✓ Parsed 500 terms

Validating header...
  ✓ format-version: 1.2
  ✓ ontology: biocViews

Validating terms...
  ✓ All validation checks passed!

Checking for cycles in the ontology...
  ✓ No cycles detected - ontology is a valid DAG

==================================================
VALIDATION SUCCESSFUL
==================================================
```

### Using R

If R is installed, you can also use the R validation script:

```bash
cd inst/ontology
Rscript test_ontology.R
```

## Relationship to Original DOT File

The OBO file was generated from `inst/dot/biocViewsVocab.dot` using the conversion script. The conversion preserves all structural information:

- **Nodes** → **Terms**: Each node in the DOT graph becomes an OBO term
- **Edges** → **is_a relationships**: Each edge `A -> B` becomes `B is_a A` (B is a subclass of A)
- **Hierarchy**: The parent-child relationships are maintained exactly

To regenerate the OBO file from the DOT file:

```bash
cd inst/ontology
python3 convert_dot_to_obo.py
```

## Differences from DOT Format

1. **Identifiers**: Terms have unique numeric IDs (`BIOCVIEWS:0000001`) instead of just names
2. **Definitions**: Many terms include formal definitions
3. **Metadata**: OBO format includes ontology-level metadata (version, namespace, etc.)
4. **Standardization**: OBO is a widely-used standard format compatible with ontology tools
5. **Validation**: OBO format has well-defined validation rules and tools

## Tools and Resources

### OBO Format Resources
- [OBO Format Specification](http://owlcollab.github.io/oboformat/doc/GO.format.obo-1_2.html)
- [OBO Foundry](http://www.obofoundry.org/)

### R Packages
- [ontologyIndex](https://cran.r-project.org/package=ontologyIndex) - Parse and query OBO files
- [ontoProc](https://bioconductor.org/packages/ontoProc/) - Ontology processing utilities

### Python Packages
- [pronto](https://pypi.org/project/pronto/) - Python OBO parser
- [obonet](https://pypi.org/project/obonet/) - Convert OBO to NetworkX graphs

## Future Enhancements

Potential improvements to the ontology:

1. **Additional Definitions**: Add definitions for more terms (currently 57/500 have definitions)
2. **Synonyms**: Add alternative names for terms
3. **Cross-references**: Link to external databases (e.g., GO, KEGG)
4. **Term metadata**: Add creation dates, contributors, etc.
5. **Relationships**: Beyond is_a, add other relationship types (part_of, regulates, etc.)

## Contributing

To propose changes to the ontology:

1. Modify the source DOT file: `inst/dot/biocViewsVocab.dot`
2. Regenerate the OBO file: `python3 inst/ontology/convert_dot_to_obo.py`
3. Validate the result: `python3 inst/ontology/validate_obo.py`
4. Submit a pull request with both DOT and OBO changes

## License

This ontology follows the same license as the biocViews package.
