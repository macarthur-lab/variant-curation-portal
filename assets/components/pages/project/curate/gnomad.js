import PropTypes from "prop-types";
import React from "react";
import { Header, Segment } from "semantic-ui-react";

// gnomAD is based on GRCh37. So if a variant's coordinates are based on GRCh38,
// then we need lifted over coordinates to look it up in gnomAD.
export const getGnomadVariantId = variant =>
  variant.reference_genome === "GRCh38" ? variant.liftover_variant_id : variant.variant_id;

export const GnomadVariantView = ({ variant }) => {
  const gnomadVariantId = getGnomadVariantId(variant);

  if (!gnomadVariantId) {
    return (
      <Segment placeholder textAlign="center">
        <Header>
          gnomAD variant page not available
          <br />
          No GRCh37 variant ID
        </Header>
      </Segment>
    );
  }
  return (
    <iframe
      title="gnomAD variant page"
      id="gnomad-variant"
      src={`https://gnomad.broadinstitute.org/variant/${gnomadVariantId}`}
      style={{ width: "100%", height: "3900px" }}
    />
  );
};

GnomadVariantView.propTypes = {
  variant: PropTypes.shape({
    reference_genome: PropTypes.oneOf(["GRCh37", "GRCh38"]).isRequired,
    variant_id: PropTypes.string.isRequired,
    liftover_variant_id: PropTypes.string,
  }).isRequired,
};

export const GnomadGeneView = ({ variant }) => {
  const hasAnnotations = variant.annotations.length > 0;

  if (!hasAnnotations) {
    return (
      <Segment placeholder textAlign="center">
        <Header>
          gnomAD gene page unavailable for this variant
          <br />
          No annotations
        </Header>
      </Segment>
    );
  }

  return (
    <iframe
      title="gnomAD gene page"
      id="gnomad-gene"
      src={`https://gnomad.broadinstitute.org/gene/${variant.annotations[0].gene_id}`}
      style={{ width: "100%", height: "2000px" }}
    />
  );
};

GnomadGeneView.propTypes = {
  variant: PropTypes.shape({
    annotations: PropTypes.arrayOf(
      PropTypes.shape({
        consequence: PropTypes.string.isRequired,
        gene_id: PropTypes.string.isRequired,
        gene_symbol: PropTypes.string.isRequired,
        transcript_id: PropTypes.string.isRequired,
      })
    ).isRequired,
  }).isRequired,
};
