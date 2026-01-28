"""Tests for BGee gene to expression transform."""

import pytest
from biolink_model.datamodel.pydanticmodel_v2 import GeneToExpressionSiteAssociation

from gene_to_expression import transform_bgee_data


class MockTransform:
    """Simple mock that collects written items."""

    def __init__(self):
        self.items = []

    def write(self, entity):
        self.items.append(entity)


@pytest.fixture
def bgee_test_data():
    """Test data that tests the ranking logic - multiple genes with different expression ranks."""
    return [
        # Gene 1 - should take top 2 (ranks 100, 200)
        {
            "Gene ID": "ENSG001",
            "Gene name": "Gene1",
            "Anatomical entity ID": "CL:0000001",
            "Expression": "present",
            "Expression rank": 100.0,
            "Call quality": "gold",
            "FDR": 0.01,
            "Expression score": 85.0,
        },
        {
            "Gene ID": "ENSG001",
            "Gene name": "Gene1",
            "Anatomical entity ID": "CL:0000002",
            "Expression": "present",
            "Expression rank": 200.0,
            "Call quality": "silver",
            "FDR": 0.02,
            "Expression score": 80.0,
        },
        {
            "Gene ID": "ENSG001",
            "Gene name": "Gene1",
            "Anatomical entity ID": "CL:0000003",
            "Expression": "present",
            "Expression rank": 300.0,
            "Call quality": "bronze",
            "FDR": 0.03,
            "Expression score": 75.0,
        },
        # Gene 2 - should take top 1 (rank 150)
        {
            "Gene ID": "ENSG002",
            "Gene name": "Gene2",
            "Anatomical entity ID": "UBERON:0000001",
            "Expression": "present",
            "Expression rank": 150.0,
            "Call quality": "gold",
            "FDR": 0.01,
            "Expression score": 90.0,
        },
        {
            "Gene ID": "ENSG002",
            "Gene name": "Gene2",
            "Anatomical entity ID": "UBERON:0000002",
            "Expression": "present",
            "Expression rank": 400.0,
            "Call quality": "bronze",
            "FDR": 0.04,
            "Expression score": 70.0,
        },
    ]


@pytest.fixture
def bgee_complex_anatomical_data():
    """Test data with complex anatomical entity (intersection)."""
    return [
        {
            "Gene ID": "ENSG003",
            "Gene name": "Gene3",
            "Anatomical entity ID": "UBERON:0000001 \u2229 CL:0000005",
            "Expression": "present",
            "Expression rank": 50.0,
            "Call quality": "gold",
            "FDR": 0.005,
            "Expression score": 95.0,
        }
    ]


def test_bgee_ranking_logic(bgee_test_data):
    """Test that the ranking logic works - takes top 10 (or fewer) per gene by Expression rank."""
    transform = MockTransform()

    # Call the transform function directly
    transform_bgee_data(transform, bgee_test_data)

    associations = transform.items

    # Should have 5 associations total (3 for Gene1, 2 for Gene2)
    # because we take top 10 per gene (all available when < 10)
    assert len(associations) == 5

    # Check that all are the right type
    for assoc in associations:
        assert isinstance(assoc, GeneToExpressionSiteAssociation)
        assert assoc.predicate == "biolink:expressed_in"
        assert assoc.primary_knowledge_source == "infores:bgee"
        assert "infores:monarchinitiative" in assoc.aggregator_knowledge_source

    # Check Gene1 associations (should have all 3 since < 10 total)
    gene1_assocs = [a for a in associations if a.subject == "ENSEMBL:ENSG001"]
    assert len(gene1_assocs) == 3
    gene1_objects = [a.object for a in gene1_assocs]
    assert "CL:0000001" in gene1_objects  # rank 100
    assert "CL:0000002" in gene1_objects  # rank 200
    assert "CL:0000003" in gene1_objects  # rank 300 - included since < 10 total

    # Check Gene2 associations (should have both 2 since < 10 total)
    gene2_assocs = [a for a in associations if a.subject == "ENSEMBL:ENSG002"]
    assert len(gene2_assocs) == 2
    gene2_objects = [a.object for a in gene2_assocs]
    assert "UBERON:0000001" in gene2_objects  # rank 150
    assert "UBERON:0000002" in gene2_objects  # rank 400


def test_bgee_complex_anatomical_entity(bgee_complex_anatomical_data):
    """Test handling of complex anatomical entities with intersection."""
    transform = MockTransform()

    transform_bgee_data(transform, bgee_complex_anatomical_data)

    associations = transform.items
    assert len(associations) == 1

    assoc = associations[0]
    assert isinstance(assoc, GeneToExpressionSiteAssociation)
    assert assoc.subject == "ENSEMBL:ENSG003"
    assert assoc.object == "UBERON:0000001"  # Primary anatomical entity
    assert assoc.object_specialization_qualifier == "CL:0000005"  # Secondary qualifier


def test_bgee_invalid_curie_handling():
    """Test that invalid CURIE formats are skipped."""
    invalid_data = [
        {
            "Gene ID": "ENSG004",
            "Gene name": "Gene4",
            "Anatomical entity ID": "INVALID \u2229 CL:0000001",
            "Expression": "present",
            "Expression rank": 50.0,
            "Call quality": "gold",
            "FDR": 0.01,
            "Expression score": 85.0,
        },
        {
            "Gene ID": "ENSG004",
            "Gene name": "Gene4",
            "Anatomical entity ID": "CL:0000001 \u2229 INVALID2",
            "Expression": "present",
            "Expression rank": 60.0,
            "Call quality": "gold",
            "FDR": 0.01,
            "Expression score": 85.0,
        },
    ]

    transform = MockTransform()

    transform_bgee_data(transform, invalid_data)

    # Should have no associations due to invalid CURIEs
    assert len(transform.items) == 0


def test_bgee_association_properties():
    """Test that associations have correct properties."""
    data = [
        {
            "Gene ID": "ENSG005",
            "Gene name": "Gene5",
            "Anatomical entity ID": "CL:0000540",
            "Expression": "present",
            "Expression rank": 100.0,
            "Call quality": "gold",
            "FDR": 0.01,
            "Expression score": 85.0,
        }
    ]

    transform = MockTransform()
    transform_bgee_data(transform, data)

    assert len(transform.items) == 1
    assoc = transform.items[0]

    # Check all expected properties
    assert assoc.subject == "ENSEMBL:ENSG005"
    assert assoc.object == "CL:0000540"
    assert assoc.predicate == "biolink:expressed_in"
    assert assoc.primary_knowledge_source == "infores:bgee"
    assert "infores:monarchinitiative" in assoc.aggregator_knowledge_source
    assert assoc.id.startswith("uuid:")
    # knowledge_level and agent_type can be enum or string depending on serialization
    knowledge_level = assoc.knowledge_level.value if hasattr(assoc.knowledge_level, "value") else assoc.knowledge_level
    agent_type = assoc.agent_type.value if hasattr(assoc.agent_type, "value") else assoc.agent_type
    assert knowledge_level == "knowledge_assertion"
    assert agent_type == "not_provided"


def test_bgee_top_10_ranking():
    """Test that only top 10 expressions per gene are kept."""
    # Create 15 expression entries for the same gene
    data = [
        {
            "Gene ID": "ENSG006",
            "Gene name": "Gene6",
            "Anatomical entity ID": f"CL:000000{i}",
            "Expression": "present",
            "Expression rank": float(i * 100),
            "Call quality": "gold",
            "FDR": 0.01,
            "Expression score": 85.0,
        }
        for i in range(1, 16)  # 15 entries with ranks 100, 200, ..., 1500
    ]

    transform = MockTransform()
    transform_bgee_data(transform, data)

    # Should only have 10 associations (top 10 by expression rank)
    assert len(transform.items) == 10

    # Check that the kept ones are the ones with smallest ranks (100-1000)
    objects = [a.object for a in transform.items]
    # Ranks 100 (CL:0000001) through 1000 (CL:00000010) should be kept
    for i in range(1, 11):
        expected_object = f"CL:000000{i}"
        assert expected_object in objects, f"Expected {expected_object} to be in output"

    # Ranks 1100+ (CL:00000011, etc.) should NOT be included
    for i in range(11, 16):
        unexpected_object = f"CL:000000{i}"
        assert unexpected_object not in objects, f"Unexpected {unexpected_object} in output"
