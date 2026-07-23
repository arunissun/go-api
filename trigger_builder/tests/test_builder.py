from unittest import TestCase

from trigger_builder.services.builder import build_deterministic_draft


class DeterministicBuilderTests(TestCase):
    def test_blank_unit_is_omitted(self):
        draft = build_deterministic_draft(
            {},
            [{
                "phase": "activation",
                "canonicalVariable": "Hydrological Flow",
                "subcategory": "Alert-stage station count",
                "operator": ">",
                "thresholdValue": "alert stage",
                "thresholdUnit": "",
                "geographyType": "station_gauge",
                "geographyLabel": ">=2 stations",
            }],
        )

        self.assertNotIn("[unit]", draft["activation"])
        self.assertIn(
            "exceeds alert stage, for Station Gauge (>=2 stations)",
            draft["activation"],
        )
