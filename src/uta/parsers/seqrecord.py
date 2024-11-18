from collections import defaultdict
from functools import cached_property
from typing import List, Optional

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
        return result

    @cached_property
    def cds_feature(self) -> Optional[SeqFeature]:
        """
        Returns the CDS feature for any coding transcript, None for any non-coding transcript.
        Some NCBI records will contain multiple CDS features. In these one CDS describes a protein
        with accession and protein sequence, the other CDS features describes a pseudogene. This method
        will preferentially choose the CDS feature with a protein sequence.
        Example:
                 CDS             422..778
                                 /gene="C6orf119"
                                 /gene_synonym="dJ427A4.2"
                                 /codon_start=1
                                 /product="chromosome 6 open reading frame 119"
                                 /protein_id="NP_001012240.1"
                                 /db_xref="GI:59276067"
                                 /db_xref="GeneID:353267"
                                 /translation="MTDTAEAVPNFEEMFASRFTENDKEYQEYLKRPPESPPIVEEWN
                                 SRAGGNQRNRGNRLQDNRQFRGRDNRWGWPSDNRSNQWHGRSWGNNYPQHRQEPYYPQ
                                 QYGHYGYNQRPPYGYY"
                 CDS             422..775
                                 /locus_tag="RP3-427A4.2-001"
                                 /note="match: proteins: Q9BTL3 Q9CQY2 Q9CWI1"
                                 /pseudo
                                 /codon_start=1
                                 /product="Novel pseudogene"
        """
        cds_features = self.features_by_type.get("CDS")
        if cds_features is None:
            return None
        else:
            # Prefer CDS with protein accession and translated sequence.
            translated_cds_features = [
                f
                for f in cds_features
                if all([key in f.qualifiers for key in ("protein_id", "translation")])
            ]
            if len(translated_cds_features) != 1:
                raise SeqRecordFeatureError("Expected one `CDS` feature at most")
            return translated_cds_features[0]

    @cached_property
    def gene_feature(self) -> SeqFeature:
        """Returns the gene feature, which should exist for all transcripts."""
        gene_features = self.features_by_type.get("gene")
        if gene_features is None or len(gene_features) != 1:
            raise SeqRecordFeatureError(f"Expected exactly one `gene` feature, for {self.id} "
                                        f"found {len(gene_features) if gene_features is not None else None}")

        return gene_features[0]

    @property
    def id(self):
        return self._sr.id

    @property
    def gene_symbol(self):
        return self.gene_feature.qualifiers["gene"][0]

    @property
    def gene_synonyms(self):
        if "gene_synonym" in self.gene_feature.qualifiers:
            return [gs.strip() for gs in self.gene_feature.qualifiers["gene_synonym"][0].split(";")]
        else:
            return []

    @property
    def gene_type(self):
        if self.cds_feature:
            return "protein-coding"
        elif "ncRNA" in self.features_by_type:
            return "ncRNA"
        elif "pseudo" in self.features_by_type:
            return "pseudo"
        elif "rRNA" in self.features_by_type:
            return "rRNA"
        elif "snoRNA" in self.features_by_type:
            return "snoRNA"
        elif "tRNA" in self.features_by_type:
            return "tRNA"
        elif "scRNA" in self.features_by_type:
            return "scRNA"
        elif "snRNA" in self.features_by_type:
            return "snRNA"
        elif "misc_RNA" in self.features_by_type:
            return "misc_RNA"
        elif "other" in self.features_by_type:
            return "other"
        else:
            return "unknown"

    @property
    def gene_id(self):
        # db_xref="GeneID:1234"
        db_xrefs = self.gene_feature.qualifiers["db_xref"]
        gene_ids = [x.partition(":")[2] for x in db_xrefs if x.startswith("GeneID:")]
        assert len(gene_ids) == 1
        return gene_ids[0]

    @property
    def db_xrefs(self):
        """
         gene            1..4577
                 /gene="A2M"
                 /gene_synonym="DKFZp779B086; FWP007; S863-7"
                 /db_xref="GeneID:2"
                 /db_xref="HPRD:00072"
                 /db_xref="MIM:103950"
        """
        db_xrefs = self.gene_feature.qualifiers["db_xref"]
        return [xref for xref in db_xrefs]

    @property
    def cds_se_i(self):
        if self.cds_feature is not None:
            return self.cds_feature.location.start.real, self.cds_feature.location.end.real
        else:
            return None

    @property
    def cds_product(self):
        if self.cds_feature is not None:
            return self.cds_feature.qualifiers["product"][0]
        else:
            return None

    @property
    def cds_protein_id(self):
        if self.cds_feature is not None:
            return self.cds_feature.qualifiers["protein_id"][0]
        else:
            return None

    @property
    def cds_translation(self):
        if self.cds_feature is not None:
            return str(self.cds_feature.qualifiers["translation"][0])
        else:
            return None

    @property
    def exons_se_i(self):
        se_i = []
        if "exon" in self.features_by_type:
            exons = self.features_by_type["exon"]
            se_i = [(f.location.start.real, f.location.end.real) for f in exons]
        return se_i

    @property
    def codon_table(self) -> Optional[str]:
        if self.cds_feature is None:
            return None
        else:
            # default codon table is the standard table, aka "1"
            # https://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi
            return "1"

    @property
    def transl_except(self) -> Optional[List[str]]:
        if self.cds_feature is None:
            return None
        else:
            return self.cds_feature.qualifiers.get("transl_except")

    @property
    def feature_seq(self):
        return str(self._sr.seq)
