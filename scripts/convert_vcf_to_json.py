#!/usr/bin/env python3

# pip install PyVCF==0.6.8 tqdm==4.31.1

import argparse
import gzip
import json

from tqdm import tqdm
import vcf


RANKED_CONSEQUENCE_TERMS = [
    "transcript_ablation",
    "splice_acceptor_variant",
    "splice_donor_variant",
    "stop_gained",
    "frameshift_variant",
    "stop_lost",
    "start_lost",  # new in v81
    "initiator_codon_variant",  # deprecated
    "transcript_amplification",
    "inframe_insertion",
    "inframe_deletion",
    "missense_variant",
    "protein_altering_variant",  # new in v79
    "splice_region_variant",
    "incomplete_terminal_codon_variant",
    "stop_retained_variant",
    "synonymous_variant",
    "coding_sequence_variant",
    "mature_miRNA_variant",
    "5_prime_UTR_variant",
    "3_prime_UTR_variant",
    "non_coding_transcript_exon_variant",
    "non_coding_exon_variant",  # deprecated
    "intron_variant",
    "NMD_transcript_variant",
    "non_coding_transcript_variant",
    "nc_transcript_variant",  # deprecated
    "upstream_gene_variant",
    "downstream_gene_variant",
    "TFBS_ablation",
    "TFBS_amplification",
    "TF_binding_site_variant",
    "regulatory_region_ablation",
    "regulatory_region_amplification",
    "feature_elongation",
    "regulatory_region_variant",
    "feature_truncation",
    "intergenic_variant",
]

CONSEQUENCE_TERM_RANK = {term: rank for rank, term in enumerate(RANKED_CONSEQUENCE_TERMS)}


def get_rank(annotation):
    terms = annotation["Consequence"].split("&")
    return min(CONSEQUENCE_TERM_RANK.get(t) for t in terms)


def convert_vcf_to_json(vcf_path, output_path, max_samples_per_genotype=5):
    variants = {}

    with gzip.open(vcf_path, "rt") as vcf_file:
        reader = vcf.Reader(vcf_file)

        csq_header = (
            reader.infos["CSQ"]  # pylint: disable=unsubscriptable-object
            .desc.split("Format: ")[1]
            .split("|")
        )

        for row in tqdm(reader, unit=" rows"):
            samples = list(row.samples)

            # Parse CSQ field
            vep_annotations = [dict(zip(csq_header, v.split("|"))) for v in row.INFO.get("CSQ", [])]

            # Filter to only LoF annotations
            lof_annotations = [
                annotation
                for annotation in vep_annotations
                if get_rank(annotation) <= CONSEQUENCE_TERM_RANK.get("frameshift_variant")
            ]

            # Sort annotations by severity
            lof_annotations = sorted(lof_annotations, key=get_rank)

            variant_id = "-".join(map(str, [row.CHROM, row.POS, row.REF, row.ALT[0]]))

            if not lof_annotations:
                print(f"Skipping {variant_id}, no LoF annotations")
                continue

            if variant_id not in variants:
                variants[variant_id] = {
                    "variant_id": variant_id,
                    "qc_filter": (row.FILTER.join(",") if row.FILTER else "PASS"),
                    "AC": row.INFO["AC"],
                    "AN": row.INFO["AN"],
                    "AF": row.INFO["AF"],
                    "annotations": [],
                    "samples": [],
                }

            variant = variants[variant_id]

            for annotation in lof_annotations:
                variant["annotations"].append(
                    {
                        "consequence": annotation["Consequence"],
                        "gene_id": annotation["Gene"],
                        "gene_symbol": annotation["SYMBOL"],
                        "transcript_id": annotation["Feature"],
                    }
                )

            for sample in sorted(samples, key=lambda s: s["GQ"] if s["GQ"] is not None else 0):
                if sample["GT"] not in {"0/1", "1/1"}:
                    continue

                if (
                    sum(1 for s in variant["samples"] if s["GT"] == sample["GT"])
                    >= max_samples_per_genotype
                ):
                    continue

                ad_ref = sample["AD"][0]
                ad_alt = sum(sample["AD"][1:])
                allele_balance = ad_alt / float(sample["DP"]) if sample["DP"] > 0 else float("NaN")

                variant["samples"].append(
                    {
                        "sample_id": len(variant["samples"]),
                        "GT": sample["GT"],
                        "DP": sample["DP"],
                        "GQ": sample["GQ"],
                        "AD_REF": ad_ref,
                        "AD_ALT": ad_alt,
                        "AB": allele_balance,
                    }
                )

    with open(output_path, "w") as output_file:
        json.dump(list(variants.values()), output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("vcf_path")
    parser.add_argument("output_path")
    parser.add_argument("--max-samples-per-genotype", type=int, default=5)

    args = parser.parse_args()
    convert_vcf_to_json(
        args.vcf_path, args.output_path, max_samples_per_genotype=args.max_samples_per_genotype
    )