"""Tests for FoodSure AI SaaS Dashboard, Analytics, Notifications, Bilingual i18n & Settings."""

import unittest
from datetime import datetime, timezone
import pandas as pd

from backend.analytics_service import (
    get_activity_timeline,
    get_daily_insights,
    get_dashboard_kpis,
    get_dataset_class_distribution,
    get_prediction_distribution,
)
from backend.history import clear_user_history, save_analysis
from backend.notifications import (
    add_notification,
    clear_user_notifications,
    delete_notification,
    get_unread_count,
    get_user_notifications,
    init_notifications_db,
    mark_all_as_read,
    mark_as_read,
)
from backend.settings import (
    get_user_settings,
    init_settings_db,
    save_user_settings,
)
from ui.i18n import (
    TRANSLATIONS,
    get_current_language,
    set_current_language,
    t,
)


class TestBilingualTranslations(unittest.TestCase):
    def test_english_keys_exist(self):
        self.assertEqual(t("nav_dashboard"), "Dashboard")
        self.assertEqual(t("nav_analyze"), "Analyze Sample")
        self.assertEqual(t("nav_notifications"), "Notifications")
        self.assertEqual(t("nav_settings"), "Settings")

    def test_hindi_translations_exist(self):
        set_current_language("hi")
        self.assertEqual(t("nav_dashboard"), "डैशबोर्ड")
        self.assertEqual(t("nav_analyze"), "नमूने का विश्लेषण")
        self.assertEqual(t("nav_notifications"), "सूचनाएँ")
        self.assertEqual(t("nav_settings"), "सेटिंग्स")
        # Reset back to English
        set_current_language("en")

    def test_translation_interpolation(self):
        set_current_language("en")
        msg = t("dash_welcome", name="Aarav")
        self.assertIn("Aarav", msg)

        set_current_language("hi")
        msg_hi = t("dash_welcome", name="Aarav")
        self.assertIn("Aarav", msg_hi)
        self.assertIn("स्वागत", msg_hi)
        set_current_language("en")

    def test_missing_key_fallback(self):
        self.assertEqual(t("non_existent_key_xyz", default="Fallback"), "Fallback")


class TestNotificationSubsystem(unittest.TestCase):
    def setUp(self):
        init_notifications_db()
        self.user_1 = "test_user_notif_1"
        self.user_2 = "test_user_notif_2"
        clear_user_notifications(self.user_1)
        clear_user_notifications(self.user_2)

    def tearDown(self):
        clear_user_notifications(self.user_1)
        clear_user_notifications(self.user_2)

    def test_add_and_retrieve_notification(self):
        nid = add_notification(
            user_id=self.user_1,
            title="Analysis Complete",
            message="Sample T0S01 was analyzed successfully.",
            category="success",
        )
        self.assertIsNotNone(nid)

        notifs = get_user_notifications(self.user_1)
        self.assertEqual(len(notifs), 1)
        self.assertEqual(notifs[0]["title"], "Analysis Complete")
        self.assertEqual(notifs[0]["is_read"], 0)
        self.assertEqual(get_unread_count(self.user_1), 1)

    def test_notification_user_isolation(self):
        add_notification(self.user_1, "For User 1", "Message 1")
        add_notification(self.user_2, "For User 2", "Message 2")

        n1 = get_user_notifications(self.user_1)
        n2 = get_user_notifications(self.user_2)

        self.assertEqual(len(n1), 1)
        self.assertEqual(n1[0]["title"], "For User 1")
        self.assertEqual(len(n2), 1)
        self.assertEqual(n2[0]["title"], "For User 2")

    def test_unread_count_and_mark_as_read(self):
        nid1 = add_notification(self.user_1, "Alert 1", "Msg 1")
        nid2 = add_notification(self.user_1, "Alert 2", "Msg 2")

        self.assertEqual(get_unread_count(self.user_1), 2)

        ok = mark_as_read(nid1, self.user_1)
        self.assertTrue(ok)
        self.assertEqual(get_unread_count(self.user_1), 1)

        # User 2 cannot mark User 1's notification as read
        ok_unauth = mark_as_read(nid2, self.user_2)
        self.assertFalse(ok_unauth)
        self.assertEqual(get_unread_count(self.user_1), 1)

    def test_mark_all_as_read(self):
        add_notification(self.user_1, "Alert 1", "Msg 1")
        add_notification(self.user_1, "Alert 2", "Msg 2")
        self.assertEqual(get_unread_count(self.user_1), 2)

        count = mark_all_as_read(self.user_1)
        self.assertEqual(count, 2)
        self.assertEqual(get_unread_count(self.user_1), 0)

    def test_idempotency_dedupe_key(self):
        """Deduplication key prevents duplicate notifications on Streamlit reruns."""
        dedupe = "analysis_sample_123"
        nid1 = add_notification(self.user_1, "Alert", "Msg", dedupe_key=dedupe)
        nid2 = add_notification(self.user_1, "Alert", "Msg", dedupe_key=dedupe)

        self.assertEqual(nid1, nid2)
        notifs = get_user_notifications(self.user_1)
        self.assertEqual(len(notifs), 1)


class TestUserSettingsSubsystem(unittest.TestCase):
    def setUp(self):
        init_settings_db()
        self.user_id = "test_user_settings_1"

    def test_default_settings(self):
        cfg = get_user_settings("non_existent_user_abc")
        self.assertEqual(cfg["language"], "en")
        self.assertEqual(cfg["explanation_depth"], "detailed")
        self.assertEqual(cfg["notify_analysis"], 1)

    def test_save_and_retrieve_settings(self):
        save_user_settings(
            self.user_id,
            {
                "language": "hi",
                "explanation_depth": "technical",
                "explanation_lang": "hi",
                "notify_analysis": 0,
                "notify_insights": 1,
                "theme": "dark",
            },
        )
        cfg = get_user_settings(self.user_id)
        self.assertEqual(cfg["language"], "hi")
        self.assertEqual(cfg["explanation_depth"], "technical")
        self.assertEqual(cfg["explanation_lang"], "hi")
        self.assertEqual(cfg["notify_analysis"], 0)


class TestAnalyticsAndInsights(unittest.TestCase):
    def setUp(self):
        self.user_id = "test_user_analytics_1"
        clear_user_history(self.user_id)

    def tearDown(self):
        clear_user_history(self.user_id)

    def test_get_dashboard_kpis_empty(self):
        kpis = get_dashboard_kpis(self.user_id)
        self.assertEqual(kpis["total_analyses"], 0)
        self.assertEqual(kpis["analyses_today"], 0)
        self.assertEqual(kpis["pure_count"], 0)
        self.assertEqual(kpis["adulterated_count"], 0)
        self.assertGreaterEqual(kpis["dataset_sample_count"], 350)

    def test_get_dashboard_kpis_populated(self):
        save_analysis(
            user_id=self.user_id,
            sample_id="T0S01",
            input_source="Dataset",
            modality="FTIR",
            predicted_class="0%",
            predicted_percentage=0.01,
            actual_level=0.0,
            status="PURE TURMERIC",
            confidence_note="",
            analysis_mode="deterministic_fallback",
            summary="Pure sample",
            full_report={},
        )
        save_analysis(
            user_id=self.user_id,
            sample_id="T3S01",
            input_source="Dataset",
            modality="FTIR",
            predicted_class="3%",
            predicted_percentage=3.1,
            actual_level=3.0,
            status="ADULTERATED",
            confidence_note="",
            analysis_mode="deterministic_fallback",
            summary="Adulterated sample",
            full_report={},
        )

        kpis = get_dashboard_kpis(self.user_id)
        self.assertEqual(kpis["total_analyses"], 2)
        self.assertEqual(kpis["pure_count"], 1)
        self.assertEqual(kpis["adulterated_count"], 1)
        self.assertAlmostEqual(kpis["avg_predicted_percent"], 1.56, places=1)

    def test_get_activity_timeline(self):
        df = get_activity_timeline(self.user_id, days=7)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 7)
        self.assertIn("Date", df.columns)
        self.assertIn("Analyses", df.columns)

    def test_get_prediction_distribution(self):
        save_analysis(
            user_id=self.user_id,
            sample_id="T5S01",
            input_source="Dataset",
            modality="FTIR",
            predicted_class="5%",
            predicted_percentage=5.0,
            actual_level=5.0,
            status="ADULTERATED",
            confidence_note="",
            analysis_mode="deterministic_fallback",
            summary="5% sample",
            full_report={},
        )
        df = get_prediction_distribution(self.user_id)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 7)
        row_5 = df[df["Adulteration Class"] == "5%"]
        self.assertEqual(row_5["Count"].iloc[0], 1)

    def test_get_dataset_class_distribution(self):
        df = get_dataset_class_distribution()
        self.assertEqual(len(df), 7)
        self.assertEqual(df["Total Benchmark"].sum(), 350)
        self.assertEqual(df["Training Split (280)"].sum(), 280)
        self.assertEqual(df["Holdout Split (70)"].sum(), 70)

    def test_get_daily_insights_english_and_hindi(self):
        insights_en = get_daily_insights(self.user_id, lang="en")
        self.assertGreaterEqual(len(insights_en), 3)
        self.assertIn("title", insights_en[0])
        self.assertIn("body", insights_en[0])

        insights_hi = get_daily_insights(self.user_id, lang="hi")
        self.assertGreaterEqual(len(insights_hi), 3)
        # Should contain Hindi script characters
        has_devanagari = any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in insights_hi[0]["body"])
        self.assertTrue(has_devanagari, "Hindi daily insights should contain Devanagari script")


if __name__ == "__main__":
    unittest.main()
