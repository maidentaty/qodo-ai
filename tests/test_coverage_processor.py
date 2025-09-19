import xml.etree.ElementTree as ET

import pytest

from cover_agent.coverage_processor import CoverageProcessor


@pytest.fixture
def mock_xml_tree(monkeypatch):
    """
    Creates a mock function to simulate the ET.parse method, returning a mocked XML tree structure.
    """

    def mock_parse(file_path):
        # Mock XML structure for the test
        xml_str = """<coverage>
                        <packages>
                            <package>
                                <classes>
                                    <class filename="app.py">
                                        <lines>
                                            <line number="1" hits="1"/>
                                            <line number="2" hits="0"/>
                                        </lines>
                                    </class>
                                    <class filename="app.py">
                                        <lines>
                                            <line number="3" hits="1"/>
                                            <line number="4" hits="0"/>
                                        </lines>
                                    </class>
                                </classes>
                            </package>
                        </packages>
                     </coverage>"""
        root = ET.ElementTree(ET.fromstring(xml_str))
        return root

    monkeypatch.setattr(ET, "parse", mock_parse)


class TestCoverageProcessor:
    """
    Test suite for the CoverageProcessor class.
    """

    @pytest.fixture
    def processor(self):
        """
        Initializes CoverageProcessor with cobertura coverage type for each test.
        """
        return CoverageProcessor("fake_path", "app.py", "cobertura")

    def test_parse_coverage_report_cobertura(self, mock_xml_tree, processor):
        """
        Tests the parse_coverage_report method for correct line number and coverage calculation with Cobertura reports.
        """
        covered_lines, missed_lines, coverage_pct = processor.parse_coverage_report()

        assert covered_lines == [1, 3], "Should list lines 1 and 3 as covered"
        assert missed_lines == [2, 4], "Should list lines 2 and 4 as missed"
        assert coverage_pct == 0.5, "Coverage should be 50 percent"
   

    def test_verify_report_update_file_not_exist(self, mocker):
        """
        Tests that verify_report_update raises an AssertionError if the coverage report file does not exist.
        """
        mocker.patch("os.path.exists", return_value=False)

        processor = CoverageProcessor("fake_path", "app.py", "cobertura")
        with pytest.raises(
            AssertionError,
            match='Fatal: Coverage report "fake_path" was not generated.',
        ):
            processor.verify_report_update(1234567890)

    def test_process_coverage_report(self, mocker):
        """
        Tests the process_coverage_report method for verifying and parsing the coverage report.
        """
        mock_verify = mocker.patch("cover_agent.coverage_processor.CoverageProcessor.verify_report_update")
        mock_parse = mocker.patch(
            "cover_agent.coverage_processor.CoverageProcessor.parse_coverage_report",
            return_value=([], [], 0.0),
        )

        processor = CoverageProcessor("fake_path", "app.py", "cobertura")
        result = processor.process_coverage_report(1234567890)

        mock_verify.assert_called_once_with(1234567890)
        mock_parse.assert_called_once()
        assert result == ([], [], 0.0), "Expected result to be ([], [], 0.0)"

    def test_parse_coverage_report_cobertura_filename_not_found(self, mock_xml_tree, processor):
        """
        Tests that parse_coverage_report_cobertura returns empty lists and 0 coverage when the file is not found.
        """
        covered_lines, missed_lines, coverage_pct = processor.parse_coverage_report_cobertura("non_existent_file.py")
        assert covered_lines == [], "Expected no covered lines"
        assert missed_lines == [], "Expected no missed lines"
        assert coverage_pct == 0.0, "Expected 0% coverage"

    def test_parse_coverage_report_cobertura_all_files(self, mock_xml_tree, processor):
        """
        Tests that parse_coverage_report_cobertura returns coverage data for all files.
        """
        coverage_data = processor.parse_coverage_report_cobertura()
        expected_data = {"app.py": ([1, 3], [2, 4], 0.5)}
        assert coverage_data == expected_data, "Expected coverage data for all files"

    
    def test_parse_coverage_report_unsupported_type_without_feature_flag(self):
        """
        Tests that parse_coverage_report raises a ValueError for unsupported coverage report types when the feature flag is disabled.
        """
        processor = CoverageProcessor(
            "fake_path",
            "app.py",
            "unsupported_type",
            use_report_coverage_feature_flag=False,
        )
        with pytest.raises(ValueError, match="Unsupported coverage report type: unsupported_type"):
            processor.parse_coverage_report()

    
    def test_parse_json_diff_coverage_report(self, mocker):
        """
        Tests parsing of JSON diff coverage report.
        """
        # Mock JSON data
        mock_json_data = {
            "src_stats": {
                "path/to/app.py": {
                    "covered_lines": [1, 3, 5],
                    "violation_lines": [2, 4, 6],
                    "percent_covered": 50.0,
                }
            }
        }

        # Mock open and json.load
        mock_open = mocker.patch("builtins.open", mocker.mock_open())
        mocker.patch("json.load", return_value=mock_json_data)

        # Create processor with diff_coverage_report_path
        processor = CoverageProcessor(
            "fake_path",
            "path/to/app.py",
            "diff_cover_json",
            diff_coverage_report_path="diff_coverage.json",
        )

        # Call the method
        covered_lines, missed_lines, coverage_pct = processor.parse_json_diff_coverage_report()

        # Verify results
        assert covered_lines == [1, 3, 5]
        assert missed_lines == [2, 4, 6]
        assert coverage_pct == 0.5

        # Test with file not found in report
        processor = CoverageProcessor(
            "fake_path",
            "path/to/nonexistent.py",
            "diff_cover_json",
            diff_coverage_report_path="diff_coverage.json",
        )

        covered_lines, missed_lines, coverage_pct = processor.parse_json_diff_coverage_report()

        # Verify default values returned
        assert covered_lines == []
        assert missed_lines == []
        assert coverage_pct == 0.0
