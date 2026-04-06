import json
import unittest
from collections import Counter
from pathlib import Path

from langchain.messages import HumanMessage

from agent.graph.apify_places_agent import ApifyPlacesAgent
from agent.graph.formatter_agent import FormatterAgent


FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "agent"
    / "static_data"
    / "apify"
    / "default.json"
)


def load_fixture_items():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class FormatterAgentTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_items = load_fixture_items()

    def setUp(self):
        self.agent = FormatterAgent(default_city="Austin, TX")

    async def test_formatter_call_returns_expected_ui_fields_for_first_item(self):
        result = await self.agent(
            {
                "messages": [
                    HumanMessage(
                        content=json.dumps([self.fixture_items[0]], ensure_ascii=False)
                    )
                ]
            }
        )

        payload = json.loads(result["messages"][-1].content)
        self.assertEqual(len(payload), 1)

        item = payload[0]
        self.assertEqual(item["restaurantId"], "ChIJp7tO_dy1RIYRW9_xLOG_ehs")
        self.assertEqual(item["name"], "Sapori Italian Roots")
        self.assertEqual(item["detail"], "Restaurant")
        self.assertEqual(item["rating"], "4.8 | 753 ratings")
        self.assertEqual(item["address"], "800 Brazos St ste 215, Austin, TX 78701")
        self.assertEqual(item["infoLink"], "https://saporiatx.com/")
        self.assertEqual(
            item["infoLinkMarkdown"],
            "[Visit site](https://saporiatx.com/)",
        )
        self.assertEqual(item["tags"], "Serves local specialty | Cozy | Lunch")
        self.assertAlmostEqual(item["lat"], 30.2698335)
        self.assertAlmostEqual(item["lng"], -97.7412877)
        self.assertNotIn("reservationUrl", item)

    async def test_formatter_preserves_precise_links_and_reservation_url(self):
        result = await self.agent(
            {
                "messages": [
                    HumanMessage(
                        content=json.dumps([self.fixture_items[1]], ensure_ascii=False)
                    )
                ]
            }
        )

        item = json.loads(result["messages"][-1].content)[0]
        self.assertEqual(item["restaurantId"], "ChIJndqjXQBLW4YR4e4Edn7JQ_8")
        self.assertEqual(item["detail"], "Italian restaurant")
        self.assertEqual(item["infoLink"], "https://www.figaustin.com/")
        self.assertTrue(
            item["reservationUrl"].startswith("https://www.google.com/maps/reserve/")
        )
        self.assertEqual(item["tags"], "Live music | Great cocktails | Great dessert")

    async def test_formatter_tag_selection_is_deterministic_across_runs(self):
        state = {
            "messages": [
                HumanMessage(
                    content=json.dumps(self.fixture_items[:12], ensure_ascii=False)
                )
            ]
        }

        first = await self.agent(state)
        second = await self.agent(state)
        self.assertEqual(first["messages"][-1].content, second["messages"][-1].content)

    async def test_formatter_limits_duplicate_visible_tag_pairs(self):
        result = await self.agent(
            {
                "messages": [
                    HumanMessage(
                        content=json.dumps(self.fixture_items, ensure_ascii=False)
                    )
                ]
            }
        )

        payload = json.loads(result["messages"][-1].content)
        visible_pair_counts = Counter()
        for item in payload:
            tags = [tag.strip() for tag in item["tags"].split("|") if tag.strip()]
            if len(tags) >= 2:
                visible_pair_counts[" | ".join(tags[:2])] += 1

        self.assertLessEqual(max(visible_pair_counts.values(), default=0), 2)

    async def test_formatter_prefers_specific_categories_over_generic_category_name(
        self,
    ):
        normalized = self.agent._normalize_item(
            {
                "title": "Test Place",
                "categoryName": "Restaurant",
                "categories": ["Italian restaurant", "Pizza restaurant"],
                "address": "123 Main St, Austin, TX",
                "url": "https://www.google.com/maps/place/test",
            }
        )

        self.assertEqual(normalized["detail"], "Italian restaurant, Pizza restaurant")
        self.assertEqual(
            normalized["infoLink"], "https://www.google.com/maps/place/test"
        )

    async def test_formatter_generates_maps_search_link_when_precise_links_are_missing(
        self,
    ):
        normalized = self.agent._normalize_item(
            {
                "title": "No Link Bistro",
                "categoryName": "Bistro",
                "address": "55 Test Ave, Austin, TX 78701",
            }
        )

        self.assertEqual(
            normalized["infoLink"],
            "https://www.google.com/maps/search/?api=1&query=No+Link+Bistro+55+Test+Ave%2C+Austin%2C+TX+78701",
        )
        self.assertEqual(
            normalized["infoLinkMarkdown"],
            "[Visit site](https://www.google.com/maps/search/?api=1&query=No+Link+Bistro+55+Test+Ave%2C+Austin%2C+TX+78701)",
        )


class ApifySelectionTests(unittest.TestCase):
    def test_sample_items_orders_by_rank_and_is_stable(self):
        items = [
            {"title": "Third", "rank": 3},
            {"title": "Missing"},
            {"title": "First", "rank": 1},
            {"title": "Second", "rank": 2},
        ]

        sampled = ApifyPlacesAgent._sample_items(items, 3)
        self.assertEqual(
            [item["title"] for item in sampled],
            ["First", "Second", "Third"],
        )

    def test_sample_items_preserves_original_order_when_ranks_are_missing(self):
        items = [
            {"title": "Alpha"},
            {"title": "Beta"},
            {"title": "Gamma"},
        ]

        sampled = ApifyPlacesAgent._sample_items(items, 2)
        self.assertEqual([item["title"] for item in sampled], ["Alpha", "Beta"])


if __name__ == "__main__":
    unittest.main()
