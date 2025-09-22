import csv
import json
import os
import re
import xml.etree.ElementTree as ET

from typing import List, Optional, Tuple, Union

from cover_agent.custom_logger import CustomLogger
from cover_agent.settings.config_schema import CoverageType


class CoverageProcessor:
    def __init__(
        self,
        file_path: str,
        src_file_path: str,
        coverage_type: CoverageType,
        use_report_coverage_feature_flag: bool = False,
        diff_coverage_report_path: str = None,
        logger: Optional[CustomLogger] = None,
        generate_log_files: bool = True,
    ):
        """
        Initializes a CoverageProcessor object.

        Args:
            file_path (str): The path to the coverage report file.
            src_file_path (str): The fully qualified path of the file for which coverage data is being processed.
            coverage_type (CoverageType): The type of coverage report being processed.
            logger (CustomLogger): The logger object for logging messages.
            generate_log_files (bool): Whether or not to generate logs.

        Attributes:
            file_path (str): The path to the coverage report file.
            src_file_path (str): The fully qualified path of the file for which coverage data is being processed.
            coverage_type (CoverageType): The type of coverage report being processed.
            logger (CustomLogger): The logger object for logging messages.

        Returns:
            None
        """
        self.file_path = file_path
        self.src_file_path = src_file_path
        self.coverage_type = coverage_type
        self.logger = logger or CustomLogger.get_logger(__name__, generate_log_files=generate_log_files)
        self.use_report_coverage_feature_flag = use_report_coverage_feature_flag
        self.diff_coverage_report_path = diff_coverage_report_path

    def process_coverage_report(self, time_of_test_command: int) -> Tuple[list, list, float]:
        """
        Verifies the coverage report's existence and update time, and then
        parses the report based on its type to extract coverage data.

        Args:
            time_of_test_command (int): The time the test command was run, in milliseconds.

        Returns:
            Tuple[list, list, float]: A tuple containing lists of covered and missed line numbers, and the coverage percentage.
        """
        self.verify_report_update(time_of_test_command)
        return self.parse_coverage_report()

    def verify_report_update(self, time_of_test_command: int):
        """
        Verifies the coverage report's existence and update time.

        Args:
            time_of_test_command (int): The time the test command was run, in milliseconds.

        Raises:
            AssertionError: If the coverage report does not exist or was not updated after the test command.
        """
        assert os.path.exists(self.file_path), f'Fatal: Coverage report "{self.file_path}" was not generated.'

        # Convert file modification time to milliseconds for comparison
        file_mod_time_ms = int(round(os.path.getmtime(self.file_path) * 1000))

        if not file_mod_time_ms > time_of_test_command:
            self.logger.warning(
                f"The coverage report file was not updated after the test command. file_mod_time_ms: {file_mod_time_ms}, time_of_test_command: {time_of_test_command}. {file_mod_time_ms > time_of_test_command}"
            )

    def parse_coverage_report(self) -> Tuple[list, list, float]:
        """
        Parses a code coverage report to extract covered and missed line numbers for a specific file,
        and calculates the coverage percentage, based on the specified coverage report type.

        Returns:
            Tuple[list, list, float]: A tuple containing lists of covered and missed line numbers, and the coverage percentage.
        """
        if self.use_report_coverage_feature_flag:
            if self.coverage_type == "cobertura":
                return self.parse_coverage_report_cobertura()
            elif self.coverage_type == "lcov":
                return self.parse_coverage_report_lcov()
            else:
                raise ValueError(f"Unsupported coverage report type: {self.coverage_type}")
        else:
            if self.coverage_type == "cobertura":
                # Default behavior is to parse out a single file from the report
                return self.parse_coverage_report_cobertura(filename=os.path.basename(self.src_file_path))
            elif self.coverage_type == "lcov":
                return self.parse_coverage_report_lcov()
            elif self.coverage_type == "diff_cover_json":
                return self.parse_json_diff_coverage_report()
            else:
                raise ValueError(f"Unsupported coverage report type: {self.coverage_type}")

    def parse_coverage_report_cobertura(self, filename: str = None) -> Union[Tuple[list, list, float], dict]:
        """
        Parses a Cobertura XML code coverage report to extract covered and missed line numbers
        for a specific file or for all files (if filename is None). Aggregates coverage data from
        multiple <class> entries that share the same filename.

        Args:
            filename (str, optional): Filename to process. If None, process all files.

        Returns:
            If filename is provided, returns (covered_lines, missed_lines, coverage_percent).
            If filename is None, returns a dict: { filename: (covered_lines, missed_lines, coverage_percent) }.
        """
        tree = ET.parse(self.file_path)
        root = tree.getroot()

        if filename:
            # Collect coverage for all <class> elements matching the given filename
            all_covered, all_missed = [], []
            for cls in root.findall(".//class"):
                name_attr = cls.get("filename")
                if name_attr and name_attr.endswith(filename):
                    c_covered, c_missed, _ = self.parse_coverage_data_for_class(cls)
                    all_covered.extend(c_covered)
                    all_missed.extend(c_missed)

            # Deduplicate and compute coverage
            covered_set = set(all_covered)
            missed_set = set(all_missed) - covered_set
            total_lines = len(covered_set) + len(missed_set)
            coverage_percentage = (len(covered_set) / total_lines) if total_lines else 0

            return list(covered_set), list(missed_set), coverage_percentage

        else:
            # Collect coverage for every <class>, grouping by filename
            coverage_data = {}
            file_map = {}  # filename -> ([covered], [missed])

            for cls in root.findall(".//class"):
                cls_filename = cls.get("filename")
                if cls_filename:
                    c_covered, c_missed, _ = self.parse_coverage_data_for_class(cls)
                    if cls_filename not in file_map:
                        file_map[cls_filename] = ([], [])
                    file_map[cls_filename][0].extend(c_covered)
                    file_map[cls_filename][1].extend(c_missed)

            # Convert raw lists to sets, compute coverage, store results
            for f_name, (c_covered, c_missed) in file_map.items():
                covered_set = set(c_covered)
                missed_set = set(c_missed) - covered_set
                total_lines = len(covered_set) + len(missed_set)
                coverage_percentage = (len(covered_set) / total_lines) if total_lines else 0
                coverage_data[f_name] = (
                    list(covered_set),
                    list(missed_set),
                    coverage_percentage,
                )

            return coverage_data

    def parse_coverage_data_for_class(self, cls) -> Tuple[list, list, float]:
        """
        Parses coverage data for a single class.

        Args:
            cls (Element): XML element representing the class.

        Returns:
            Tuple[list, list, float]: A tuple containing lists of covered and missed line numbers,
                                    and the coverage percentage.
        """
        lines_covered, lines_missed = [], []

        for line in cls.findall(".//line"):
            line_number = int(line.get("number"))
            hits = int(line.get("hits"))
            if hits > 0:
                lines_covered.append(line_number)
            else:
                lines_missed.append(line_number)

        total_lines = len(lines_covered) + len(lines_missed)
        coverage_percentage = (len(lines_covered) / total_lines) if total_lines > 0 else 0

        return lines_covered, lines_missed, coverage_percentage

    def parse_coverage_report_lcov(self):

        lines_covered, lines_missed = [], []
        filename = os.path.basename(self.src_file_path)
        try:
            with open(self.file_path, "r") as file:
                for line in file:
                    line = line.strip()
                    if line.startswith("SF:"):
                        if line.endswith(filename):
                            for line in file:
                                line = line.strip()
                                if line.startswith("DA:"):
                                    line_number = line.replace("DA:", "").split(",")[0]
                                    hits = line.replace("DA:", "").split(",")[1]
                                    if int(hits) > 0:
                                        lines_covered.append(int(line_number))
                                    else:
                                        lines_missed.append(int(line_number))
                                elif line.startswith("end_of_record"):
                                    break

        except (FileNotFoundError, IOError) as e:
            self.logger.error(f"Error reading file {self.file_path}: {e}")
            raise

        total_lines = len(lines_covered) + len(lines_missed)
        coverage_percentage = (len(lines_covered) / total_lines) if total_lines > 0 else 0

        return lines_covered, lines_missed, coverage_percentage

    def parse_json_diff_coverage_report(self) -> Tuple[List[int], List[int], float]:
        """
        Parses a JSON-formatted diff coverage report to extract covered lines, missed lines,
        and the coverage percentage for the specified src_file_path.
        Returns:
            Tuple[List[int], List[int], float]: A tuple containing lists of covered and missed lines,
                                                and the coverage percentage.
        """
        with open(self.diff_coverage_report_path, "r") as file:
            report_data = json.load(file)

        # Create relative path components of `src_file_path` for matching
        src_relative_path = os.path.relpath(self.src_file_path)
        src_relative_components = src_relative_path.split(os.sep)

        # Initialize variables for covered and missed lines
        relevant_stats = None

        for file_path, stats in report_data["src_stats"].items():
            # Split the JSON's file path into components
            file_path_components = file_path.split(os.sep)

            # Match if the JSON path ends with the same components as `src_file_path`
            if file_path_components[-len(src_relative_components) :] == src_relative_components:
                relevant_stats = stats
                break

        # If a match is found, extract the data
        if relevant_stats:
            covered_lines = relevant_stats["covered_lines"]
            violation_lines = relevant_stats["violation_lines"]
            coverage_percentage = relevant_stats["percent_covered"] / 100  # Convert to decimal
        else:
            # Default values if the file isn't found in the report
            covered_lines = []
            violation_lines = []
            coverage_percentage = 0.0

        return covered_lines, violation_lines, coverage_percentage

    def get_file_extension(self, filename: str) -> str | None:
        """Get the file extension from a given filename."""
        return os.path.splitext(filename)[1].lstrip(".")
