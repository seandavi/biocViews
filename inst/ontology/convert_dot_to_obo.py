#!/usr/bin/env python3
"""
Convert biocViewsVocab.dot file to OBO ontology format.
"""

import re
from collections import defaultdict
from datetime import datetime

def parse_dot_file(filename):
    """Parse DOT file and extract nodes and edges."""
    edges = []
    nodes = set()
    edges_set = set()  # Track unique edges to avoid duplicates
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line.startswith('/*') or line.startswith('*') or line.startswith('//') or not line:
                continue
            # Skip digraph and closing brace
            if line.startswith('digraph') or line == '}':
                continue
            
            # Parse edges: A -> B;
            edge_match = re.match(r'(\w+)\s*->\s*(\w+);?', line)
            if edge_match:
                source, target = edge_match.groups()
                edge = (source, target)
                # Only add unique edges (removes duplicates from source DOT file)
                if edge not in edges_set:
                    edges.append(edge)
                    edges_set.add(edge)
                nodes.add(source)
                nodes.add(target)
    
    return nodes, edges

def create_term_definitions():
    """Create definitions for terms where meaning can be inferred."""
    definitions = {
        'BiocViews': 'Root term for the Bioconductor Views ontology, a controlled vocabulary for categorizing Bioconductor packages.',
        'Software': 'Bioconductor software packages providing tools for computational biology and bioinformatics analysis.',
        'AnnotationData': 'Annotation data packages containing curated biological metadata, reference information, and mapping data.',
        'ExperimentData': 'Experimental data packages containing example datasets, published research data, and reproducible research materials.',
        'Workflow': 'Workflow packages demonstrating complete analysis pipelines and best practices for common bioinformatics tasks.',
        
        # Technology terms
        'Technology': 'Laboratory and computational technologies used in biological research.',
        'Sequencing': 'High-throughput DNA or RNA sequencing technologies.',
        'RNASeq': 'Sequencing technology for analyzing RNA transcripts to study gene expression and transcriptome dynamics.',
        'DNASeq': 'Whole genome or targeted DNA sequencing for variant discovery and genomic analysis.',
        'ChIPSeq': 'Chromatin immunoprecipitation followed by sequencing for genome-wide analysis of protein-DNA interactions.',
        'ATACSeq': 'Assay for Transposase-Accessible Chromatin using sequencing to identify open chromatin regions.',
        'Microarray': 'Hybridization-based technologies for high-throughput measurement of gene expression or genomic features.',
        'FlowCytometry': 'Technology for measuring physical and chemical characteristics of cells or particles in a fluid stream.',
        'MassSpectrometry': 'Analytical technique for identifying and quantifying molecules based on mass-to-charge ratio.',
        'SingleCell': 'Technologies and methods for analyzing individual cells rather than bulk populations.',
        'Spatial': 'Technologies for spatially-resolved molecular profiling of tissues.',
        
        # Research fields
        'ResearchField': 'Broad scientific research areas and disciplines.',
        'Genomics': 'Study of complete genomes and their function.',
        'Proteomics': 'Large-scale study of proteins, their structures, and functions.',
        'Metabolomics': 'Comprehensive analysis of metabolites in biological systems.',
        'Epigenetics': 'Study of heritable changes in gene expression without DNA sequence alterations.',
        'Transcriptomics': 'Study of the complete set of RNA transcripts in a cell or population.',
        'Metagenomics': 'Study of genetic material recovered directly from environmental samples.',
        'Lipidomics': 'Large-scale study of lipid pathways and networks in biological systems.',
        'Immunology': 'Study of the immune system and immune responses.',
        'SystemsBiology': 'Computational and mathematical modeling of complex biological systems.',
        
        # Biological questions
        'BiologicalQuestion': 'Specific biological questions or analyses addressed by bioinformatics methods.',
        'DifferentialExpression': 'Analysis to identify genes with statistically significant differences in expression levels between conditions.',
        'GeneSetEnrichment': 'Statistical methods to identify coordinated changes in predefined sets of genes.',
        'VariantDetection': 'Identification of genetic variants including SNPs, indels, and structural variations.',
        'PeakDetection': 'Identification of enriched genomic regions from sequencing data.',
        'AlternativeSplicing': 'Analysis of differential exon usage and transcript isoform expression.',
        'GenomeAssembly': 'Reconstruction of genome sequences from short sequencing reads.',
        
        # Workflow steps
        'WorkflowStep': 'Common steps and procedures in bioinformatics analysis workflows.',
        'Alignment': 'Mapping sequencing reads or sequences to a reference genome or transcriptome.',
        'Preprocessing': 'Initial data processing steps including quality control and normalization.',
        'QualityControl': 'Assessment and filtering of data quality.',
        'Normalization': 'Statistical procedures to remove systematic technical variation.',
        'Visualization': 'Graphical representation of data and analysis results.',
        'Annotation': 'Addition of biological context and functional information to genomic features.',
        
        # Statistical methods
        'StatisticalMethod': 'Statistical and computational methods used in bioinformatics analysis.',
        'Clustering': 'Grouping of similar data points or samples.',
        'Classification': 'Assignment of samples or features to predefined categories.',
        'DimensionReduction': 'Techniques to reduce the number of variables while preserving information.',
        'Bayesian': 'Statistical methods based on Bayesian probability theory.',
        
        # Organisms
        'Organism': 'Biological species for which annotation or data packages are available.',
        'Homo_sapiens': 'Human species.',
        'Mus_musculus': 'House mouse.',
        'Rattus_norvegicus': 'Norway rat.',
        'Drosophila_melanogaster': 'Fruit fly.',
        'Caenorhabditis_elegans': 'Nematode worm.',
        'Saccharomyces_cerevisiae': 'Budding yeast.',
        'Arabidopsis_thaliana': 'Thale cress plant.',
        'Danio_rerio': 'Zebrafish.',
        
        # Package types
        'PackageType': 'Types of annotation data packages in Bioconductor.',
        'OrgDb': 'Organism-level annotation databases linking gene identifiers to functional information.',
        'TxDb': 'Transcript-level annotation databases containing gene models and transcript structures.',
        'BSgenome': 'Full genome sequence packages for specific organisms.',
    }
    return definitions

def assign_term_ids(nodes, edges):
    """Assign numeric IDs to terms in a hierarchical manner."""
    # Build parent-child relationships
    children = defaultdict(list)
    parents = defaultdict(list)
    
    for source, target in edges:
        children[source].append(target)
        parents[target].append(source)
    
    # Find root node (should be BiocViews)
    root = None
    for node in nodes:
        if node not in parents:
            root = node
            break
    
    if root is None:
        # Fallback: use BiocViews if found
        root = 'BiocViews' if 'BiocViews' in nodes else list(nodes)[0]
    
    # BFS traversal to assign IDs
    term_ids = {}
    id_counter = 1
    queue = [root]
    visited = set()
    
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        
        term_ids[current] = f"BIOCVIEWS:{id_counter:07d}"
        id_counter += 1
        
        # Add children to queue (sorted for consistency)
        if current in children:
            queue.extend(sorted(children[current]))
    
    # Add any remaining nodes that weren't reached
    for node in sorted(nodes):
        if node not in term_ids:
            term_ids[node] = f"BIOCVIEWS:{id_counter:07d}"
            id_counter += 1
    
    return term_ids

def write_obo_file(output_filename, nodes, edges):
    """Write OBO format file."""
    term_ids = assign_term_ids(nodes, edges)
    definitions = create_term_definitions()
    
    # Build parent-child relationships
    children_map = defaultdict(list)
    for source, target in edges:
        children_map[target].append(source)
    
    with open(output_filename, 'w') as f:
        # Write header
        f.write("format-version: 1.2\n")
        f.write("data-version: 1.0\n")
        f.write(f"date: {datetime.now().strftime('%d:%m:%Y %H:%M')}\n")
        f.write("ontology: biocViews\n")
        f.write("default-namespace: biocViews\n")
        f.write("\n")
        
        # Write terms
        for node in sorted(nodes, key=lambda x: term_ids[x]):
            f.write("[Term]\n")
            f.write(f"id: {term_ids[node]}\n")
            f.write(f"name: {node}\n")
            
            # Add definition if available
            if node in definitions:
                f.write(f'def: "{definitions[node]}" []\n')
            
            # Add is_a relationships (in OBO, child is_a parent)
            if node in children_map:
                for parent in sorted(children_map[node]):
                    f.write(f"is_a: {term_ids[parent]} ! {parent}\n")
            
            f.write("\n")

def main():
    dot_file = '../dot/biocViewsVocab.dot'
    obo_file = 'biocViewsVocab.obo'
    
    print(f"Parsing {dot_file}...")
    nodes, edges = parse_dot_file(dot_file)
    
    print(f"Found {len(nodes)} terms and {len(edges)} relationships")
    
    print(f"Writing OBO file to {obo_file}...")
    write_obo_file(obo_file, nodes, edges)
    
    print("Conversion complete!")
    print(f"\nSummary:")
    print(f"  Terms: {len(nodes)}")
    print(f"  Relationships: {len(edges)}")

if __name__ == '__main__':
    main()
