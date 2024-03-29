from collections import defaultdict
from functools import cached_property
from typing import Union

import Bio.SeqRecord
from Bio.SeqFeature import SeqFeature


class SeqRecordFeatureError(Exception):
    """Raised when SeqRecord does not have the expected features."""


class SeqRecordFacade:

    def __init__(self, seqrecord: Bio.SeqRecord.SeqRecord):
        self._sr = seqrecord

    @cached_property
    def features_by_type(self) -> dict[str, list]:
        result = defaultdict(list)
        for feat in self._sr.features:
            result[feat.type].append(feat)
        self.validate_features_by_type(result)
        return result

    @staticmethod
    def validate_features_by_type(features: dict[str, list]) -> None:
        """Raise exceptions if feature mapping is invalid."""
        if "CDS" in features and len(features["CDS"]) > 1:
            raise SeqRecordFeatureError("Expected one `CDS` feature at most")
        if "gene" not in features or len(features["gene"]) != 1:
            raise SeqRecordFeatureError("Expected exactly one `gene` feature")

    @cached_property
    def gene_feature(self) -> SeqFeature:
        """Returns the gene feature, which is assumed to exist for all transcripts. """
        return self.features_by_type.get("gene")[0]

    @property
    def id(self):
        return self._sr.id

    @property
    def gene_symbol(self):
        return self.gene_feature.qualifiers["gene"][0]

    @property
    def gene_id(self):
        # db_xref="GeneID:1234"
        db_xrefs = self.gene_feature.qualifiers["db_xref"]
        gene_ids = [x.partition(":")[2] for x in db_xrefs if x.startswith("GeneID:")]
        assert len(gene_ids) == 1
        return gene_ids[0]

    @property
    def cds_se_i(self):
        if self.features_by_type.get("CDS"):
            cds_feature = self.features_by_type.get("CDS")[0]
            return (cds_feature.location.start.real, cds_feature.location.end.real)
        else:
            return None

    @property
    def exons_se_i(self):
        if "exon" in self.features_by_type:
            exons = self.features_by_type["exon"]
        else:
            exons = [self.gene_feature]
        return [(f.location.start.real, f.location.end.real) for f in exons]
