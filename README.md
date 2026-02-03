# bgee-ingest

Bgee is a database for retrieval and comparison of gene expression patterns across multiple animal species, produced from multiple data types (bulk RNA-Seq, single-cell RNA-Seq, Affymetrix, in situ hybridization, and EST data) and from multiple data sets (including GTEx data).

## Gene Expression

This ingest uses the Bgee simple gene expression file. Files are named by Species ID.

**Source data model:**
- Gene name
- Anatomical entity ID
- Anatomical entity name
- Expression
- Call quality
- FDR
- Expression score
- Expression rank

**Biolink Captured:**

- `biolink:GeneToExpressionSiteAssociation`
    - id (random uuid, generated)
    - subject (`Gene ID`)
    - predicate (`biolink:expressed_in`, constant)
    - object (`Anatomical entity ID`)
    - aggregating_knowledge_source (`["infores:monarchinitiative", "infores:bgee"]`)

## Design Decisions

We elected to use the simple gene expression file for ease of use and because the advanced file doesn't contain much more data we are likely to use.
We could potentially import `has evidence` from the advanced file comparing `Affimetrix expression` and `RNA-Seq expression` but this doesn't seem valuable at this time.
Stage and Strain information is also available in the all_conditions file. We have elected to not import the stage information due to multiple duplicate edges based on strain.

## Setup

```bash
just setup
```

## Usage

### Download source data

```bash
just download
```

### Run transforms

```bash
# Run all transforms
just transform-all

# Run specific transform
just transform <transform_name>
```

### Run tests

```bash
just test
```

## Adding New Ingests

Use the `create-koza-ingest` Claude skill to add new ingests to this repository.

## Citation

Bastian FB, Roux J, Niknejad A, Comte A, Fonseca Costa SS, Mendes de Farias T, Moretti S, Parmentier G, Rech de Laval V, Rosikiewicz M, Wollbrett J, Echchiki A, Escoriza A, Gharib W, Gonzales-Porta M, Jarosz Y, Laurenczy B, Moret P, Person E, Roelli P, Sanjeev K, Seppey M, Robinson-Rechavi M. The Bgee suite: integrated curated expression atlas and comparative transcriptomics in animals. Nucleic Acids Research, Volume 49, Issue D1, 8 January 2021, Pages D831-D847.

## License

BSD-3-Clause
