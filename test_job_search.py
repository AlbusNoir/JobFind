#!/usr/bin/env python3
import unittest
from job_search import parse_radius, parse_keywords, clean_description, score_job, format_location

class TestJobSearchHelpers(unittest.TestCase):
    def test_parse_radius(self):
        self.assertEqual(parse_radius("25 miles"), 25)
        self.assertEqual(parse_radius("50"), 50)
        self.assertEqual(parse_radius("10mi"), 10)
        self.assertEqual(parse_radius(""), 25)
        self.assertEqual(parse_radius(None), 25)
        self.assertEqual(parse_radius("no digits"), 25)

    def test_parse_keywords(self):
        self.assertEqual(parse_keywords("it, network, support"), ["it", "network", "support"])
        self.assertEqual(parse_keywords("  helpdesk , sec+ "), ["helpdesk", "sec+"])
        self.assertEqual(parse_keywords(""), [])
        self.assertEqual(parse_keywords(None), [])

    def test_clean_description(self):
        # HTML tag stripping
        html_desc = "<p>This is a <b>great</b> job listing!</p>"
        self.assertEqual(clean_description(html_desc), "This is a great job listing!")
        
        # Whitespace normalization
        space_desc = "Line 1\nLine 2    with spaces"
        self.assertEqual(clean_description(space_desc), "Line 1 Line 2 with spaces")
        
        # Truncation (using the 160-character limit with '...')
        long_desc = "A" * 200
        truncated = clean_description(long_desc)
        self.assertEqual(len(truncated), 163) # 160 + '...'
        self.assertTrue(truncated.endswith("..."))
        
        # Generic preamble and boilerplate filtering
        boilerplate_desc = "We are seeking a candidate. Reasonable accommodations may be made. Duties include, but are not limited to installing software."
        # Should skip the preambles and pick up "installing software" fallback or the sentence "We are seeking a candidate."
        syn = clean_description(boilerplate_desc)
        self.assertNotIn("Reasonable accommodations", syn)
        self.assertNotIn("but are not limited to", syn)
        
        # Company praddle filtering
        praddle_desc = "Smurfit Westrock (NYSE:SW) is the go-to leader in sustainable packaging. We are dedicated to creating scalable paper. The Collaboration Engineer will maintain servers and support teams."
        syn2 = clean_description(praddle_desc, "Smurfit Westrock")
        self.assertNotIn("sustainable packaging", syn2)
        self.assertNotIn("We are dedicated", syn2)
        self.assertIn("maintain servers and support teams", syn2)
        
        # Empty inputs
        self.assertEqual(clean_description(None), "No description available.")
        self.assertEqual(clean_description(""), "No description available.")

    def test_format_location(self):
        row_both = {'city': 'Macon', 'state': 'GA'}
        self.assertEqual(format_location(row_both), "Macon, GA")
        
        row_city = {'city': 'Macon', 'state': None}
        self.assertEqual(format_location(row_city), "Macon")
        
        row_state = {'city': None, 'state': 'Georgia'}
        self.assertEqual(format_location(row_state), "Georgia")
        
        row_none = {'city': None, 'state': None}
        self.assertEqual(format_location(row_none), "N/A")

    def test_score_job(self):
        keywords = ["it", "network", "sec+"]
        
        # High score for matching keywords in title
        row1 = {'title': 'IT Network Engineer', 'description': 'Some description', 'company': 'Corp'}
        # "it" (10) + "network" (10) = 20
        self.assertEqual(score_job(row1, keywords), 20)
        
        # Lower score for matching keywords in description
        row2 = {'title': 'Developer', 'description': 'Requires sec+ certification and network knowledge.', 'company': 'Corp'}
        # "sec+" (1) + "network" (1) = 2
        self.assertEqual(score_job(row2, keywords), 2)
        
        # Company match score
        row3 = {'title': 'Staff', 'description': 'Description', 'company': 'IT Solutions'}
        # "it" in company (3)
        self.assertEqual(score_job(row3, keywords), 3)

if __name__ == "__main__":
    unittest.main()
