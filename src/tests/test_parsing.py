# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import copy
import os
import sys
import unittest
from typing import Dict, List, Optional

from pathpicker import format, parse
from pathpicker.formatted_text import FormattedText
from tests.lib.local_test_cases import LOCAL_TEST_CASES


class ParsingTestCase:
    def __init__(
        self,
        test_input: str,
        match: bool,
        file: Optional[str] = None,
        num: int = 0,
        validate_file_exists=False,
        disable_fuzz_test=False,
        working_dir: Optional[str] = None,
    ):
        self.input = test_input
        self.match = match
        assert not match or file is not None, "file must be set for match"
        self.file = file
        self.num = num
        self.validate_file_exists = validate_file_exists
        self.disable_fuzz_test = disable_fuzz_test
        self.working_dir = working_dir


FILE_TEST_CASES: List[ParsingTestCase] = [
    ParsingTestCase("html/js/hotness.js", True, "html/js/hotness.js"),
    ParsingTestCase(
        "/absolute/path/to/something.txt", True, "/absolute/path/to/something.txt"
    ),
    ParsingTestCase("/html/js/hotness.js42", True, "/html/js/hotness.js42"),
    ParsingTestCase("/html/js/hotness.js", True, "/html/js/hotness.js"),
    ParsingTestCase("./asd.txt:83", True, "./asd.txt", num=83),
    ParsingTestCase(".env.local", True, ".env.local"),
    ParsingTestCase(".gitignore", True, ".gitignore"),
    ParsingTestCase("tmp/.gitignore", True, "tmp/.gitignore"),
    ParsingTestCase(".ssh/.gitignore", True, ".ssh/.gitignore"),
    # For now, don't worry about matching the following case perfectly,
    # simply because it's complicated.
    #    'input': '~/.ssh/known_hosts',
    #    'match': True,
    ParsingTestCase(".ssh/known_hosts", True, ".ssh/known_hosts"),
    # Arbitrarily ignore really short dot filenames
    ParsingTestCase(".a", False),
    ParsingTestCase(
        "flib/asd/ent/berkeley/two.py-22", True, "flib/asd/ent/berkeley/two.py", num=22
    ),
    ParsingTestCase("flib/foo/bar", True, "flib/foo/bar"),
    # note space
    ParsingTestCase("flib/foo/bar ", True, "flib/foo/bar"),
    ParsingTestCase("foo/b ", True, "foo/b"),
    ParsingTestCase("foo/bar/baz/", False),
    ParsingTestCase("flib/ads/ads.thrift", True, "flib/ads/ads.thrift"),
    ParsingTestCase("banana hanana Wilde/ads/story.m", True, "Wilde/ads/story.m"),
    ParsingTestCase("flib/asd/asd.py two/three/four.py", True, "flib/asd/asd.py"),
    ParsingTestCase("asd/asd/asd/ 23", False),
    ParsingTestCase("foo/bar/TARGETS:23", True, "foo/bar/TARGETS", num=23),
    ParsingTestCase("foo/bar/TARGETS-24", True, "foo/bar/TARGETS", num=24),
    ParsingTestCase(
        'fbcode/search/places/scorer/PageScorer.cpp:27:46:#include "search/places/scorer/linear_scores/MinutiaeVerbScorer.h',
        True,
        "fbcode/search/places/scorer/PageScorer.cpp",
        num=27,
    ),
    ParsingTestCase(
        '(fbcode/search/places/scorer/PageScorer.cpp:27:46):#include "search/places/scorer/linear_scores/MinutiaeVerbScorer.h',
        True,
        "fbcode/search/places/scorer/PageScorer.cpp",
        num=27,
    ),
    # Pretty intense case
    ParsingTestCase(
        'fbcode/search/places/scorer/TARGETS:590:28:    srcs = ["linear_scores/MinutiaeVerbScorer.cpp"]',
        True,
        "fbcode/search/places/scorer/TARGETS",
        num=590,
    ),
    ParsingTestCase(
        'fbcode/search/places/scorer/TARGETS:1083:27:      "linear_scores/test/MinutiaeVerbScorerTest.cpp"',
        True,
        "fbcode/search/places/scorer/TARGETS",
        num=1083,
    ),
    ParsingTestCase("~/foo/bar/something.py", True, "~/foo/bar/something.py"),
    ParsingTestCase(
        "~/foo/bar/inHomeDir.py:22", True, "~/foo/bar/inHomeDir.py", num=22
    ),
    ParsingTestCase(
        "blarge assets/retina/victory@2x.png", True, "assets/retina/victory@2x.png"
    ),
    ParsingTestCase(
        "~/assets/retina/victory@2x.png", True, "~/assets/retina/victory@2x.png"
    ),
    ParsingTestCase("So.many.periods.txt", True, "So.many.periods.txt"),
    ParsingTestCase("So.many.periods.txt~", True, "So.many.periods.txt~"),
    ParsingTestCase("#So.many.periods.txt#", True, "#So.many.periods.txt#"),
    ParsingTestCase("SO.MANY.PERIODS.TXT", True, "SO.MANY.PERIODS.TXT"),
    ParsingTestCase(
        "blarg blah So.MANY.PERIODS.TXT:22", True, "So.MANY.PERIODS.TXT", num=22
    ),
    ParsingTestCase("SO.MANY&&PERIODSTXT", False),
    ParsingTestCase(
        "test src/categories/NSDate+Category.h",
        True,
        "src/categories/NSDate+Category.h",
    ),
    ParsingTestCase(
        "~/src/categories/NSDate+Category.h", True, "~/src/categories/NSDate+Category.h"
    ),
    ParsingTestCase(
        "M    ./inputs/evilFile With Space.txt",
        True,
        "./inputs/evilFile With Space.txt",
        validate_file_exists=True,
    ),
    ParsingTestCase(
        "./inputs/evilFile With Space.txt:22",
        True,
        "./inputs/evilFile With Space.txt",
        num=22,
        validate_file_exists=True,
    ),
    ParsingTestCase(
        "./inputs/annoying Spaces Folder/evilFile With Space2.txt",
        True,
        "./inputs/annoying Spaces Folder/evilFile With Space2.txt",
        validate_file_exists=True,
    ),
    ParsingTestCase(
        "./inputs/annoying Spaces Folder/evilFile With Space2.txt:42",
        True,
        "./inputs/annoying Spaces Folder/evilFile With Space2.txt",
        num=42,
        validate_file_exists=True,
    ),
    # with leading space
    ParsingTestCase(
        " ./inputs/annoying Spaces Folder/evilFile With Space2.txt:42",
        True,
        "./inputs/annoying Spaces Folder/evilFile With Space2.txt",
        num=42,
        validate_file_exists=True,
    ),
    # git style
    ParsingTestCase(
        "M     ./inputs/annoying Spaces Folder/evilFile With Space2.txt:42",
        True,
        "./inputs/annoying Spaces Folder/evilFile With Space2.txt",
        num=42,
        validate_file_exists=True,
    ),
    # files with + in them, silly objective c
    ParsingTestCase(
        "M     ./objectivec/NSArray+Utils.h", True, "./objectivec/NSArray+Utils.h"
    ),
    ParsingTestCase("NSArray+Utils.h", True, "NSArray+Utils.h"),
    # And with filesystem validation just in case
    # the + breaks something
    ParsingTestCase(
        "./inputs/NSArray+Utils.h:42",
        True,
        "./inputs/NSArray+Utils.h",
        num=42,
        validate_file_exists=True,
    ),
    # and our hyphen extension file
    ParsingTestCase(
        "./inputs/blogredesign.sublime-workspace:42",
        True,
        "./inputs/blogredesign.sublime-workspace",
        num=42,
        validate_file_exists=True,
    ),
    # and our hyphen extension file with no dir
    ParsingTestCase(
        "inputs/blogredesign.sublime-workspace:42",
        True,
        "inputs/blogredesign.sublime-workspace",
        num=42,
        validate_file_exists=True,
    ),
    # and our hyphen extension file with no dir or number
    ParsingTestCase(
        "inputs/blogredesign.sublime-workspace",
        True,
        "inputs/blogredesign.sublime-workspace",
        validate_file_exists=True,
    ),
    # and a huge combo of stuff
    ParsingTestCase(
        "./inputs/annoying-hyphen-dir/Package Control.system-bundle",
        True,
        "./inputs/annoying-hyphen-dir/Package Control.system-bundle",
        validate_file_exists=True,
    ),
    # and a huge combo of stuff with no prepend
    ParsingTestCase(
        "inputs/annoying-hyphen-dir/Package Control.system-bundle",
        True,
        "inputs/annoying-hyphen-dir/Package Control.system-bundle",
        validate_file_exists=True,
        disable_fuzz_test=True,
    ),
    # and a huge combo of stuff with line
    ParsingTestCase(
        "./inputs/annoying-hyphen-dir/Package Control.system-bundle:42",
        True,
        "./inputs/annoying-hyphen-dir/Package Control.system-bundle",
        num=42,
        validate_file_exists=True,
    ),
    ParsingTestCase(
        "./inputs/svo (install the zip, not me).xml",
        True,
        "./inputs/svo (install the zip, not me).xml",
        validate_file_exists=True,
    ),
    ParsingTestCase(
        "./inputs/svo (install the zip not me).xml",
        True,
        "./inputs/svo (install the zip not me).xml",
        validate_file_exists=True,
    ),
    ParsingTestCase(
        "./inputs/svo install the zip, not me.xml",
        True,
        "./inputs/svo install the zip, not me.xml",
        validate_file_exists=True,
    ),
    ParsingTestCase(
        "./inputs/svo install the zip not me.xml",
        True,
        "./inputs/svo install the zip not me.xml",
        validate_file_exists=True,
    ),
    ParsingTestCase(
        "./inputs/annoyingTildeExtension.txt~:42",
        True,
        "./inputs/annoyingTildeExtension.txt~",
        num=42,
        validate_file_exists=True,
    ),
    ParsingTestCase(
        "inputs/.DS_KINDA_STORE",
        True,
        "inputs/.DS_KINDA_STORE",
        validate_file_exists=True,
    ),
    ParsingTestCase(
        "./inputs/.DS_KINDA_STORE",
        True,
        "./inputs/.DS_KINDA_STORE",
        validate_file_exists=True,
    ),
    ParsingTestCase(
        "evilFile No Prepend.txt",
        True,
        "evilFile No Prepend.txt",
        validate_file_exists=True,
        disable_fuzz_test=True,
        working_dir="inputs",
    ),
    ParsingTestCase(
        "file-from-yocto_%.bbappend",
        True,
        "file-from-yocto_%.bbappend",
        validate_file_exists=True,
        working_dir="inputs",
    ),
    ParsingTestCase(
        "otehr thing ./foo/file-from-yocto_3.1%.bbappend",
        True,
        "file-from-yocto_3.1%.bbappend",
        validate_file_exists=True,
        working_dir="inputs",
    ),
    ParsingTestCase(
        "./file-from-yocto_3.1%.bbappend",
        True,
        "./file-from-yocto_3.1%.bbappend",
        validate_file_exists=True,
        working_dir="inputs",
    ),
    ParsingTestCase(
        "Gemfile", True, "Gemfile", validate_file_exists=False, disable_fuzz_test=True
    ),
    ParsingTestCase(
        "Gemfilenope", False, validate_file_exists=False, disable_fuzz_test=True
    ),
]

# local test cases get added as well
FILE_TEST_CASES += LOCAL_TEST_CASES

PREPEND_DIR_TEST_CASES: List[Dict[str, str]] = [
    {"in": "home/absolute/path.py", "out": "/home/absolute/path.py"},
    {
        "in": "~/www/asd.py",
        "out": os.path.expanduser("~/www/asd.py"),
    },
    {
        "in": "www/asd.py",
        "out": os.path.expanduser("~/www/asd.py"),
    },
    {"in": "foo/bar/baz/asd.py", "out": parse.PREPEND_PATH + "foo/bar/baz/asd.py"},
    {"in": "a/foo/bar/baz/asd.py", "out": parse.PREPEND_PATH + "foo/bar/baz/asd.py"},
    {"in": "b/foo/bar/baz/asd.py", "out": parse.PREPEND_PATH + "foo/bar/baz/asd.py"},
    {"in": "", "out": ""},
]


class AllInputTestCase:
    def __init__(self, test_input: str, match: Optional[str]):
        self.input = test_input
        self.match = match


ALL_INPUT_TEST_CASES: List[AllInputTestCase] = [
    AllInputTestCase("    ", None),
    AllInputTestCase(" ", None),
    AllInputTestCase("a", "a"),
    AllInputTestCase("   a", "a"),
    AllInputTestCase("a    ", "a"),
    AllInputTestCase("    foo bar", "foo bar"),
    AllInputTestCase("foo bar    ", "foo bar"),
    AllInputTestCase("    foo bar    ", "foo bar"),
    AllInputTestCase("foo bar baz", "foo bar baz"),
    AllInputTestCase(
        "	modified:   Classes/Media/YPMediaLibraryViewController.m",
        "modified:   Classes/Media/YPMediaLibraryViewController.m",
    ),
    AllInputTestCase(
        'no changes added to commit (use "git add" and/or "git commit -a")',
        'no changes added to commit (use "git add" and/or "git commit -a")',
    ),
]

# Current directory
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestParseFunction(unittest.TestCase):
    def testPrependDir(self):
        for testCase in PREPEND_DIR_TEST_CASES:
            inFile = testCase["in"]

            result = parse.prepend_dir(inFile)
            expected = testCase["out"]
            if inFile[0:2] == "~/":
                expected = os.path.expanduser(expected)

            self.assertEqual(expected, result)
        print("Tested %d dir cases." % len(PREPEND_DIR_TEST_CASES))

    def testFileFuzz(self):
        befores = ["M ", "Modified: ", "Changed: ", "+++ ", "Banana asdasdoj pjo "]
        afters = [
            " * Adapts AdsErrorCodestore to something",
            ":0:7: var AdsErrorCodeStore",
            " jkk asdad",
        ]

        for test_case in FILE_TEST_CASES:
            if test_case.disable_fuzz_test:
                continue
            for before in befores:
                for after in afters:
                    test_input = "%s%s%s" % (before, test_case.input, after)
                    this_case = copy.copy(test_case)
                    this_case.input = test_input
                    self.checkFileResult(this_case)
        print("Tested %d cases for file fuzz." % len(FILE_TEST_CASES))

    def testUnresolvable(self):
        file_line = ".../something/foo.py"
        result = parse.matchLine(file_line)
        line_obj = format.LineMatch(FormattedText(file_line), result, 0)
        self.assertTrue(
            not line_obj.isResolvable(), '"%s" should not be resolvable' % file_line
        )
        print("Tested unresolvable case.")

    def testResolvable(self):
        to_check = [case for case in FILE_TEST_CASES if case.match]
        for test_case in to_check:
            result = parse.matchLine(test_case.input)
            line_obj = format.LineMatch(FormattedText(test_case.input), result, 0)
            self.assertTrue(
                line_obj.isResolvable(),
                'Line "%s" was not resolvable' % test_case.input,
            )
        print("Tested %d resolvable cases." % len(to_check))

    def testFileMatch(self):
        for test_case in FILE_TEST_CASES:
            self.checkFileResult(test_case)
        print("Tested %d cases." % len(FILE_TEST_CASES))

    def testAllInputMatches(self):
        for test_case in ALL_INPUT_TEST_CASES:
            result = parse.matchLine(test_case.input, False, True)

            if not result:
                self.assertTrue(
                    test_case.match is None,
                    'Expected a match "%s" where one did not occur.' % test_case.match,
                )
                continue

            (match, _, _) = result
            self.assertEqual(
                match,
                test_case.match,
                'Line "%s" did not match.' % test_case.input,
            )

        print("Tested %d cases for all-input matching." % len(ALL_INPUT_TEST_CASES))

    def checkFileResult(self, test_case):
        working_dir = TESTS_DIR
        if test_case.working_dir is not None:
            working_dir = os.path.join(working_dir, test_case.working_dir)
        os.chdir(working_dir)
        result = parse.matchLine(
            test_case.input,
            validateFileExists=test_case.validate_file_exists,
        )
        if not result:
            self.assertFalse(
                test_case.match,
                'Line "%s" did not match any regex' % test_case.input,
            )
            return

        file, num, match = result
        self.assertTrue(test_case.match, 'Line "%s" did match' % test_case.input)

        self.assertEqual(
            test_case.file,
            file,
            "files not equal |%s| |%s|" % (test_case.file, file),
        )

        self.assertEqual(
            test_case.num,
            num,
            "num matches not equal %d %d for %s"
            % (test_case.num, num, test_case.input),
        )


if __name__ == "__main__":
    unittest.main()
