"""Comprehensive tests for SAP metadata enrichment."""

import pytest

from app.utils.enrichment import (
    enrich_ticket,
    extract_environment,
    extract_error_code,
    extract_tcode,
)


# ---------------------------------------------------------------------------
# extract_tcode
# ---------------------------------------------------------------------------

class TestExtractTcode:
    def test_explicit_prefix_transaction(self):
        assert extract_tcode("when I run transaction ME21N it fails") == "ME21N"

    def test_explicit_prefix_tcode_colon(self):
        assert extract_tcode("tcode: FB50 not working") == "FB50"

    def test_explicit_prefix_t_dash_code(self):
        assert extract_tcode("t-code FB60 is broken") == "FB60"

    def test_known_tcode_standalone(self):
        assert extract_tcode("MIRO invoice verification error") == "MIRO"

    def test_known_tcode_in_sentence(self):
        assert extract_tcode("FB50 posting not working, getting F5 301 error in production") == "FB50"

    def test_known_tcode_SM21(self):
        assert extract_tcode("SM21 showing lot of errors") == "SM21"

    def test_known_tcode_VF01(self):
        assert extract_tcode("VF01 billing document error") == "VF01"

    def test_sxmb_moni(self):
        result = extract_tcode("SXMB_MONI showing 50 failed IDocs")
        assert result == "SXMB_MONI"

    def test_no_tcode_vague(self):
        assert extract_tcode("system is very slow today") is None

    def test_no_tcode_pure_error(self):
        assert extract_tcode("getting F5 301 error") is None

    def test_case_insensitive_prefix(self):
        result = extract_tcode("Transaction miro is not posting")
        assert result is not None
        assert result.upper() in {"MIRO", "MIRO"}


# ---------------------------------------------------------------------------
# extract_error_code
# ---------------------------------------------------------------------------

class TestExtractErrorCode:
    def test_format1_F5_301(self):
        assert extract_error_code("getting F5 301 error in production") == "F5 301"

    def test_format1_M7_021(self):
        assert extract_error_code("ME21N failing with M7 021") == "M7 021"

    def test_format1_V1_801(self):
        assert extract_error_code("VF01 billing error V1 801") == "V1 801"

    def test_format2_AA_500(self):
        assert extract_error_code("asset depreciation run failed AA 500") == "AA 500"

    def test_format2_ME_573(self):
        assert extract_error_code("purchase order error ME 573") == "ME 573"

    def test_format2_M8_108(self):
        assert extract_error_code("goods receipt not posting M8 108") == "M8 108"

    def test_format3_ABAP_RUNTIME_ERROR(self):
        assert extract_error_code("ST22 showing ABAP_RUNTIME_ERROR") == "ABAP_RUNTIME_ERROR"

    def test_format3_SYNTAX_ERROR(self):
        assert extract_error_code("custom report crashing with SYNTAX_ERROR") == "SYNTAX_ERROR"

    def test_format3_TIME_OUT(self):
        assert extract_error_code("system throwing TIME_OUT on login") == "TIME_OUT"

    def test_format4_IDOC_ERROR(self):
        assert extract_error_code("IDoc processing failing IDOC_ERROR") == "IDOC_ERROR"

    def test_format4_XIAdapter(self):
        assert extract_error_code("XIAdapter error on PI/PO") == "XIAdapter"

    def test_no_error_vague(self):
        assert extract_error_code("system is slow") is None

    def test_no_error_no_sap(self):
        assert extract_error_code("please help with the issue") is None


# ---------------------------------------------------------------------------
# extract_environment
# ---------------------------------------------------------------------------

class TestExtractEnvironment:
    def test_PRD_exact(self):
        assert extract_environment("error in PRD system") == "PRD"

    def test_PROD_normalized(self):
        assert extract_environment("PROD is down") == "PRD"

    def test_PRODUCTION_normalized(self):
        assert extract_environment("PRODUCTION system cannot post") == "PRD"

    def test_production_system_phrase(self):
        assert extract_environment("error in production system") == "PRD"

    def test_QAS_exact(self):
        assert extract_environment("tested in QAS environment") == "QAS"

    def test_QUALITY_normalized(self):
        assert extract_environment("QUALITY server issue") == "QAS"

    def test_DEV_exact(self):
        assert extract_environment("this only happens in DEV") == "DEV"

    def test_DEVELOPMENT_normalized(self):
        assert extract_environment("running in DEVELOPMENT environment") == "DEV"

    def test_dev_box_phrase(self):
        assert extract_environment("tested on dev box") == "DEV"

    def test_no_environment_vague(self):
        assert extract_environment("system is slow") is None

    def test_case_insensitive(self):
        assert extract_environment("issue in prd") == "PRD"


# ---------------------------------------------------------------------------
# enrich_ticket (combined)
# ---------------------------------------------------------------------------

class TestEnrichTicket:
    def test_full_extraction(self):
        text = "FB50 posting not working, getting F5 301 error in production. Need urgent help."
        result = enrich_ticket(text)
        assert result["tcode"] == "FB50"
        assert result["error_code"] == "F5 301"
        assert result["environment"] == "PRD"

    def test_vague_ticket_returns_none(self):
        result = enrich_ticket("system slow")
        assert result["tcode"] is None
        assert result["error_code"] is None
        assert result["environment"] is None

    def test_partial_extraction(self):
        text = "ME21N purchase order creation failing M7 021 error"
        result = enrich_ticket(text)
        assert result["tcode"] == "ME21N"
        assert result["error_code"] == "M7 021"
        assert result["environment"] is None

    def test_returns_dict_keys(self):
        result = enrich_ticket("anything")
        assert set(result.keys()) == {"tcode", "error_code", "environment"}
