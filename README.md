# Bgee

Bgee is a database for retrieval and comparison of gene expression patterns across multiple animal species, produced from multiple data types (bulk RNA-Seq, single-cell RNA-Seq, Affymetrix, in situ hybridization, and EST data) and from multiple data sets (including GTEx data).

## [Gene Expression](#gene)

This ingest uses the Bgee simple gene expression files (v15.0), one per species. Expression data for model organisms (mouse, rat, zebrafish, frog, fly, worm) is available but currently excluded because it is obtained from other sources (e.g. Alliance). The species actively ingested are:

- Human (*Homo sapiens*)
- Cow (*Bos taurus*)
- Dog (*Canis lupus familiaris*)
- Chicken (*Gallus gallus*)
- Pig (*Sus scrofa*)

### Source File Fields

* Gene ID
* Gene name
* Anatomical entity ID
* Anatomical entity name
* Expression
* Call quality
* FDR
* Expression score
* Expression rank

### Filtering

Rows are included only when all of the following criteria are met:

- Expression is "present"
- FDR < 0.05
- Expression score > 70
- Expression rank < 10,000

After filtering, results are grouped by Gene ID and only the **top 10 rows by smallest Expression rank** are kept per gene.

When an Anatomical entity ID contains an intersection (` ∩ `), the first entity is used as the object and the second as `object_specialization_qualifier`.

### Biolink Captured

* biolink:GeneToExpressionSiteAssociation
    * id (random uuid, generated)
    * subject (ENSEMBL gene ID)
    * predicate (`biolink:expressed_in`)
    * object (Anatomical entity ID)
    * object_specialization_qualifier (second anatomical entity, when present)
    * primary_knowledge_source (`infores:bgee`)
    * aggregator_knowledge_source (`["infores:monarchinitiative"]`)
    * knowledge_level (`knowledge_assertion`)
    * agent_type (`not_provided`)

### Design Decisions

We elected to use the simple gene expression file for ease of use and because the advanced file doesn't contain much more data we are likely to use. We could potentially import `has evidence` from the advanced file comparing `Affimetrix expression` and `RNA-Seq expression` but this doesn't seem valuable at this time.

Stage and Strain information is also available in the all_conditions file. We have elected to not import the stage information due to multiple duplicate edges based on strain.

## Citation

Bastian FB, Roux J, Niknejad A, Comte A, Fonseca Costa SS, Mendes de Farias T, Moretti S, Parmentier G, Rech de Laval V, Rosikiewicz M, Wollbrett J, Echchiki A, Escoriza A, Gharib W, Gonzales-Porta M, Jarosz Y, Laurenczy B, Moret P, Person E, Roelli P, Sanjeev K, Seppey M, Robinson-Rechavi M. The Bgee suite: integrated curated expression atlas and comparative transcriptomics in animals. Nucleic Acids Research, Volume 49, Issue D1, 8 January 2021, Pages D831-D847.

## License

BSD-3-Clause
