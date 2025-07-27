#!/usr/bin/env python
import weaver
import unittest
import tempfile
import os
import json
import sys
from unittest.mock import patch
from io import StringIO


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestWeaverFunctions(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""

        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_load_config_valid_json(self):
        """Test loading a valid JSON config file."""
        config_data = {
            "patterns": ["test"],
            "words": ["admin", "user"],
            "numbers": ["123", "456"]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            f.flush()

            result = weaver.load_config(f.name)
            self.assertEqual(result, config_data)

        os.unlink(f.name)

    def test_load_config_invalid_json(self):
        """Test loading an invalid JSON config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            f.flush()

            with self.assertRaises(json.JSONDecodeError):
                weaver.load_config(f.name)

        os.unlink(f.name)

    def test_load_config_nonexistent_file(self):
        """Test loading a non-existent config file."""
        with self.assertRaises(FileNotFoundError):
            weaver.load_config("nonexistent_file.json")

    def test_load_words_file_mixed_content(self):
        """Test loading a words file with mixed content types."""
        content = """admin,user,root
password
123
456
!
@
special_word
group1,group2,group3
789
#
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()

            words, numbers, specials, groups = weaver.load_words_file(f.name)

            expected_words = ['admin', 'user', 'root', 'password',
                              'special_word', 'group1', 'group2', 'group3']
            self.assertEqual(sorted(words), sorted(expected_words))

            expected_numbers = ['123', '456', '789']
            self.assertEqual(sorted(numbers), sorted(expected_numbers))

            expected_specials = ['!', '@', '#']
            self.assertEqual(sorted(specials), sorted(expected_specials))

            expected_groups = [['admin', 'user', 'root'],
                               ['group1', 'group2', 'group3']]
            self.assertEqual(len(groups), 2)
            self.assertIn(['admin', 'user', 'root'], groups)
            self.assertIn(['group1', 'group2', 'group3'], groups)

        os.unlink(f.name)

    def test_load_words_file_empty_lines(self):
        """Test loading a words file with empty lines."""
        content = """word1

word2


123

"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()

            words, numbers, specials, groups = weaver.load_words_file(f.name)

            self.assertEqual(words, ['word1', 'word2'])
            self.assertEqual(numbers, ['123'])
            self.assertEqual(specials, [])
            self.assertEqual(groups, [])

        os.unlink(f.name)

    def test_load_words_file_nonexistent(self):
        """Test loading a non-existent words file."""
        with self.assertRaises(FileNotFoundError):
            weaver.load_words_file("nonexistent_file.txt")

    def test_load_list_from_file_valid(self):
        """Test loading a list from a valid file."""
        content = """item1
item2
item3

item4
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()

            result = weaver.load_list_from_file(f.name)
            expected = ['item1', 'item2', 'item3', 'item4']
            self.assertEqual(result, expected)

        os.unlink(f.name)

    def test_load_list_from_file_nonexistent(self):
        """Test loading a list from a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            weaver.load_list_from_file("nonexistent_file.txt")

    def test_generalize_string_unicode(self):
        """Test Unicode normalization."""

        self.assertEqual(weaver.generalize_string("résumé"), "resume")
        self.assertEqual(weaver.generalize_string("naïve"), "naive")
        self.assertEqual(weaver.generalize_string("café"), "cafe")

        self.assertEqual(weaver.generalize_string("admin"), "admin")
        self.assertEqual(weaver.generalize_string("PASSWORD"), "PASSWORD")

    def test_parse_placeholders_word_patterns(self):
        """Test parsing word placeholder patterns."""

        pattern = "{word1}{WORD2}{Word3}{word4*}"
        tokens = weaver.parse_placeholders(pattern)

        expected = [
            ('word1', 'word', 'lower'),
            ('WORD2', 'word', 'upper'),
            ('Word3', 'word', 'capitalize'),
            ('word4*', 'word', 'any')
        ]
        self.assertEqual(tokens, expected)

    def test_parse_placeholders_number_special(self):
        """Test parsing number and special placeholder patterns."""
        pattern = "{number}{special}"
        tokens = weaver.parse_placeholders(pattern)

        expected = [
            ('number', 'number', None),
            ('special', 'special', None)
        ]
        self.assertEqual(tokens, expected)

    def test_parse_placeholders_complex_pattern(self):
        """Test parsing complex patterns."""
        pattern = "{Word1}{number}{special}{word2*}{WORD3}"
        tokens = weaver.parse_placeholders(pattern)

        expected = [
            ('Word1', 'word', 'capitalize'),
            ('number', 'number', None),
            ('special', 'special', None),
            ('word2*', 'word', 'any'),
            ('WORD3', 'word', 'upper')
        ]
        self.assertEqual(tokens, expected)

    def test_parse_placeholders_no_placeholders(self):
        """Test parsing pattern with no placeholders."""
        pattern = "static_password_123"
        tokens = weaver.parse_placeholders(pattern)
        self.assertEqual(tokens, [])

    def test_fill_pattern_word_cases(self):
        """Test filling patterns with different word cases."""
        pattern = "{word1}{WORD2}{Word3}{word4*}"
        tokens = [
            ('word1', 'word', 'lower'),
            ('WORD2', 'word', 'upper'),
            ('Word3', 'word', 'capitalize'),
            ('word4*', 'word', 'any')
        ]
        values = ['ADMIN', 'password', 'ROOT', 'user']

        result = weaver.fill_pattern(pattern, tokens, values)
        expected = "adminPASSWORDRootuser"
        self.assertEqual(result, expected)

    def test_fill_pattern_mixed_types(self):
        """Test filling patterns with mixed placeholder types."""
        pattern = "{Word1}{number}{special}"
        tokens = [
            ('Word1', 'word', 'capitalize'),
            ('number', 'number', None),
            ('special', 'special', None)
        ]
        values = ['admin', '123', '!']

        result = weaver.fill_pattern(pattern, tokens, values)
        expected = "Admin123!"
        self.assertEqual(result, expected)

    def test_generate_passwords_simple_patterns(self):
        """Test generating passwords with simple patterns."""
        patterns = ["{word1}{number}"]
        words = ['admin', 'user']
        numbers = ['123', '456']
        specials = ['!', '@']

        result = weaver.generate_passwords(patterns, words, numbers, specials)

        expected = {'admin123', 'admin456', 'user123', 'user456'}
        self.assertEqual(result, expected)

    def test_generate_passwords_wildcard_words(self):
        """Test generating passwords with wildcard word patterns."""
        patterns = ["{word1*}"]
        words = ['Admin']
        numbers = []
        specials = []

        result = weaver.generate_passwords(patterns, words, numbers, specials)

        expected = {'admin', 'Admin', 'ADMIN'}
        self.assertEqual(result, expected)

    def test_generate_passwords_duplicate_words(self):
        """Test that duplicate words in same password are filtered out."""
        patterns = ["{word1}{word2}"]
        words = ['admin', 'user']
        numbers = []
        specials = []

        result = weaver.generate_passwords(patterns, words, numbers, specials)

        self.assertNotIn('adminadmin', result)
        self.assertNotIn('useruser', result)
        self.assertIn('adminuser', result)
        self.assertIn('useradmin', result)

    def test_generate_passwords_complex_patterns(self):
        """Test generating passwords with complex patterns."""
        patterns = ["{Word1}{number}{special}", "{word1*}{word2}"]
        words = ['admin', 'user']
        numbers = ['123']
        specials = ['!']

        result = weaver.generate_passwords(patterns, words, numbers, specials)

        self.assertIn('Admin123!', result)
        self.assertIn('User123!', result)
        self.assertIn('adminuser', result)
        self.assertIn('Adminuser', result)
        self.assertIn('ADMINuser', result)

    def test_filter_passwords_length_constraints(self):
        """Test filtering passwords by length constraints."""
        candidates = ['a', 'ab', 'abc', 'abcd', 'abcde']

        result = weaver.filter_passwords(candidates, 3, 100, [])
        expected = ['abc', 'abcd', 'abcde']
        self.assertEqual(sorted(result), sorted(expected))

        result = weaver.filter_passwords(candidates, 1, 3, [])
        expected = ['a', 'ab', 'abc']
        self.assertEqual(sorted(result), sorted(expected))

        result = weaver.filter_passwords(candidates, 2, 4, [])
        expected = ['ab', 'abc', 'abcd']
        self.assertEqual(sorted(result), sorted(expected))

    def test_filter_passwords_word_groups(self):
        """Test filtering passwords with word group conflicts."""
        candidates = ['adminuser', 'adminpass', 'userpass', 'admin123']
        word_groups = [['admin', 'user'], ['pass', 'password']]

        result = weaver.filter_passwords(candidates, 1, 100, word_groups)

        self.assertNotIn('adminuser', result)
        self.assertIn('adminpass', result)
        self.assertIn('userpass', result)
        self.assertIn('admin123', result)

    def test_filter_passwords_case_insensitive_groups(self):
        """Test that word group filtering is case insensitive."""
        candidates = ['AdminUser', 'ADMINPASS', 'userPASS']
        word_groups = [['admin', 'user'], ['pass', 'password']]

        result = weaver.filter_passwords(candidates, 1, 100, word_groups)

        self.assertNotIn('AdminUser', result)
        self.assertIn('ADMINPASS', result)
        self.assertIn('userPASS', result)

    def test_get_default_values(self):
        """Test getting default values."""
        defaults = weaver.get_default_values()

        self.assertIn('words', defaults)
        self.assertIn('numbers', defaults)
        self.assertIn('specials', defaults)
        self.assertIn('groups', defaults)

        self.assertIsInstance(defaults['words'], list)
        self.assertIsInstance(defaults['numbers'], list)
        self.assertIsInstance(defaults['specials'], list)
        self.assertIsInstance(defaults['groups'], list)

        self.assertIn('admin', defaults['words'])
        self.assertIn('password', defaults['words'])
        self.assertIn('1234', defaults['numbers'])
        self.assertIn('_', defaults['specials'])

    def test_parse_word_groups_single_group(self):
        """Test parsing word groups with single group."""
        value = "admin,user,root"
        words, groups = weaver.parse_word_groups(value)

        expected_words = ['admin', 'user', 'root']
        expected_groups = [['admin', 'user', 'root']]

        self.assertEqual(sorted(words), sorted(expected_words))
        self.assertEqual(groups, expected_groups)

    def test_parse_word_groups_multiple_groups(self):
        """Test parsing word groups with multiple groups."""
        value = "admin,user;pass,password;123,456"
        words, groups = weaver.parse_word_groups(value)

        expected_words = ['admin', 'user', 'pass', 'password', '123', '456']
        expected_groups = [['admin', 'user'], [
            'pass', 'password'], ['123', '456']]

        self.assertEqual(sorted(words), sorted(expected_words))
        self.assertEqual(groups, expected_groups)

    def test_parse_word_groups_whitespace_handling(self):
        """Test parsing word groups with extra whitespace."""
        value = " admin , user ; pass , password "
        words, groups = weaver.parse_word_groups(value)

        expected_words = ['admin', 'user', 'pass', 'password']
        expected_groups = [['admin', 'user'], ['pass', 'password']]

        self.assertEqual(sorted(words), sorted(expected_words))
        self.assertEqual(groups, expected_groups)

    def test_parse_word_groups_empty_groups(self):
        """Test parsing word groups with empty groups."""
        value = "admin,user;;pass,password"
        words, groups = weaver.parse_word_groups(value)

        expected_words = ['admin', 'user', 'pass', 'password']
        expected_groups = [['admin', 'user'], ['pass', 'password']]

        self.assertEqual(sorted(words), sorted(expected_words))
        self.assertEqual(groups, expected_groups)

    def test_parse_semicolon_list_normal(self):
        """Test parsing semicolon-separated list."""
        value = "item1;item2;item3"
        result = weaver.parse_semicolon_list(value)
        expected = ['item1', 'item2', 'item3']
        self.assertEqual(result, expected)

    def test_parse_semicolon_list_whitespace(self):
        """Test parsing semicolon-separated list with whitespace."""
        value = " item1 ; item2 ; item3 "
        result = weaver.parse_semicolon_list(value)
        expected = ['item1', 'item2', 'item3']
        self.assertEqual(result, expected)

    def test_parse_semicolon_list_empty_items(self):
        """Test parsing semicolon-separated list with empty items."""
        value = "item1;;item2;;"
        result = weaver.parse_semicolon_list(value)
        expected = ['item1', 'item2']
        self.assertEqual(result, expected)


class TestWeaverMainFunction(unittest.TestCase):
    """Test the main function with different argument combinations."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_main_basic_pattern(self):
        """Test main function with basic pattern."""
        output_file = os.path.join(self.temp_dir, 'test_output.txt')

        test_args = [
            'weaver',
            '--patterns', 'Wn',
            '--words', 'admin;user',
            '--numbers', '123;456',
            '--output', output_file
        ]

        with patch('sys.argv', test_args):
            weaver.main()

        self.assertTrue(os.path.exists(output_file))

        with open(output_file, 'r') as f:
            passwords = [line.strip() for line in f]

        expected_passwords = ['admin123', 'admin456', 'user123', 'user456']
        self.assertEqual(sorted(passwords), sorted(expected_passwords))

    def test_main_pattern_modes(self):
        """Test main function with different pattern modes."""

        output_file = os.path.join(self.temp_dir, 'test_any.txt')

        test_args = [
            'weaver',
            '--patterns', 'W',
            '--words', 'admin',
            '--pattern-mode', 'any',
            '--output', output_file
        ]

        with patch('sys.argv', test_args):
            weaver.main()

        with open(output_file, 'r') as f:
            passwords = [line.strip() for line in f]

        self.assertIn('admin', passwords)
        self.assertIn('Admin', passwords)
        self.assertIn('ADMIN', passwords)

    def test_main_file_inputs(self):
        """Test main function with file inputs."""

        words_file = os.path.join(self.temp_dir, 'words.txt')
        numbers_file = os.path.join(self.temp_dir, 'numbers.txt')
        specials_file = os.path.join(self.temp_dir, 'specials.txt')
        output_file = os.path.join(self.temp_dir, 'output.txt')

        with open(words_file, 'w') as f:
            f.write('admin\nuser\n')

        with open(numbers_file, 'w') as f:
            f.write('123\n456\n')

        with open(specials_file, 'w') as f:
            f.write('!\n@\n')

        test_args = [
            'weaver',
            '--patterns', 'Wns',
            '--words', f'@{words_file}',
            '--numbers', f'@{numbers_file}',
            '--specials', f'@{specials_file}',
            '--output', output_file
        ]

        with patch('sys.argv', test_args):
            weaver.main()

        self.assertTrue(os.path.exists(output_file))

        with open(output_file, 'r') as f:
            passwords = [line.strip() for line in f]

        self.assertTrue(any('admin123!' in pw for pw in passwords))
        self.assertTrue(len(passwords) > 0)

    def test_main_words_file_input(self):
        """Test main function with words file input."""
        words_file = os.path.join(self.temp_dir, 'mixed_words.txt')
        output_file = os.path.join(self.temp_dir, 'output.txt')

        with open(words_file, 'w') as f:
            f.write('admin,user\npassword\n123\n!\n')

        test_args = [
            'weaver',
            '--patterns', 'Wns',
            '--words-file', words_file,
            '--output', output_file
        ]

        with patch('sys.argv', test_args):
            weaver.main()

        self.assertTrue(os.path.exists(output_file))

        with open(output_file, 'r') as f:
            passwords = [line.strip() for line in f]

        self.assertTrue(len(passwords) > 0)

    def test_main_length_constraints(self):
        """Test main function with length constraints."""
        output_file = os.path.join(self.temp_dir, 'length_test.txt')

        test_args = [
            'weaver',
            '--patterns', 'Wns',
            '--words', 'a;verylongword',
            '--numbers', '1;12345',
            '--specials', '!',
            '--min-length', '5',
            '--max-length', '8',
            '--output', output_file
        ]

        with patch('sys.argv', test_args):
            weaver.main()

        with open(output_file, 'r') as f:
            passwords = [line.strip() for line in f]

        for pw in passwords:
            self.assertTrue(
                5 <= len(pw) <= 8, f"Password '{pw}' length {len(pw)} not in range 5-8")

    def test_main_generalize_option(self):
        """Test main function with Unicode generalization."""
        output_file = os.path.join(self.temp_dir, 'generalize_test.txt')

        test_args = [
            'weaver',
            '--patterns', 'W',
            '--words', 'café;résumé',
            '--generalize',
            '--output', output_file
        ]

        with patch('sys.argv', test_args):
            weaver.main()

        with open(output_file, 'r') as f:
            passwords = [line.strip() for line in f]

        self.assertIn('cafe', passwords)
        self.assertIn('resume', passwords)

    def test_main_verbose_output(self):
        """Test main function with verbose output."""
        output_file = os.path.join(self.temp_dir, 'verbose_test.txt')

        test_args = [
            'weaver',
            '--patterns', 'W',
            '--words', 'admin',
            '--verbose',
            '--output', output_file
        ]

        with patch('sys.argv', test_args), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            weaver.main()

    def test_main_no_patterns_error(self):
        """Test main function with no patterns provided."""
        test_args = ['weaver']

        with patch('sys.argv', test_args), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            weaver.main()

    def test_main_nonexistent_file_error(self):
        """Test main function with non-existent file inputs."""
        test_args = [
            'weaver',
            '--patterns', 'W',
            '--words', '@nonexistent_file.txt'
        ]

        with patch('sys.argv', test_args), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            weaver.main()

    def test_main_special_characters_handling(self):
        """Test main function with various special character inputs."""
        output_file = os.path.join(self.temp_dir, 'special_test.txt')

        test_args = [
            'weaver',
            '--patterns', 'Ws',
            '--words', 'test',
            '--specials', '!@#$%',
            '--output', output_file
        ]

        with patch('sys.argv', test_args):
            weaver.main()

        with open(output_file, 'r') as f:
            passwords = [line.strip() for line in f]

        self.assertTrue(any('!' in pw for pw in passwords))
        self.assertTrue(any('@' in pw for pw in passwords))

    def test_main_semicolon_separated_specials(self):
        """Test main function with semicolon-separated special characters."""
        output_file = os.path.join(self.temp_dir, 'semicolon_specials.txt')

        test_args = [
            'weaver',
            '--patterns', 'Ws',
            '--words', 'test',
            '--specials', '!;@;#',
            '--output', output_file
        ]

        with patch('sys.argv', test_args):
            weaver.main()

        with open(output_file, 'r') as f:
            passwords = [line.strip() for line in f]

        self.assertTrue(any('test!' in pw for pw in passwords))
        self.assertTrue(any('test@' in pw for pw in passwords))
        self.assertTrue(any('test#' in pw for pw in passwords))


class TestEdgeCasesAndErrorHandling(unittest.TestCase):
    """Test edge cases and error handling scenarios."""

    def test_empty_inputs(self):
        """Test behavior with empty inputs."""

        result = weaver.generate_passwords(["{word1}"], [], ['123'], ['!'])
        self.assertEqual(result, set())

        result = weaver.generate_passwords(["{number}"], ['admin'], [], ['!'])
        self.assertEqual(result, set())

        result = weaver.generate_passwords(
            ["{special}"], ['admin'], ['123'], [])
        self.assertEqual(result, set())

    def test_malformed_patterns(self):
        """Test behavior with malformed patterns."""

        tokens = weaver.parse_placeholders("{word1")
        self.assertEqual(tokens, [])

        tokens = weaver.parse_placeholders("{}")
        self.assertEqual(tokens, [])

        tokens = weaver.parse_placeholders("{invalid}")
        self.assertEqual(tokens, [])

    def test_very_long_inputs(self):
        """Test behavior with very long inputs."""

        long_words = [f'word{i}' for i in range(1000)]
        result = weaver.generate_passwords(
            ["{word1}"], long_words[:10], ['1'], ['!'])
        self.assertEqual(len(result), 10)

        long_pattern = "{word1}" * 100
        tokens = weaver.parse_placeholders(long_pattern)
        self.assertEqual(len(tokens), 100)

    def test_unicode_edge_cases(self):
        """Test Unicode edge cases."""

        self.assertEqual(weaver.generalize_string(""), "")

        self.assertEqual(weaver.generalize_string("́́́"), "")

        result = weaver.generalize_string("αβγ123")
        self.assertEqual(result, "αβγ123")

    def test_filter_passwords_edge_cases(self):
        """Test password filtering edge cases."""

        result = weaver.filter_passwords([], 1, 10, [])
        self.assertEqual(result, [])

        result = weaver.filter_passwords(['test'], 10, 5, [])
        self.assertEqual(result, [])

        result = weaver.filter_passwords(['test'], 1, 10, [])
        self.assertEqual(result, ['test'])

    def test_file_encoding_issues(self):
        """Test handling of different file encodings."""

        content = "café\nnaïve\n"
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()

            result = weaver.load_list_from_file(f.name)
            expected = ['café', 'naïve']
            self.assertEqual(result, expected)

        os.unlink(f.name)

    def test_extreme_length_constraints(self):
        """Test extreme length constraints."""
        candidates = ['a', 'ab', 'abc', 'abcdefghijklmnopqrstuvwxyz']

        result = weaver.filter_passwords(candidates, 0, 100, [])
        self.assertEqual(len(result), 4)

        result = weaver.filter_passwords(candidates, 1, 10000, [])
        self.assertEqual(len(result), 4)

        result = weaver.filter_passwords(candidates, 2, 2, [])
        self.assertEqual(result, ['ab'])

    def test_complex_word_groups(self):
        """Test complex word group scenarios."""
        candidates = ['adminuserroot', 'testpassword', 'adminsecret']
        word_groups = [
            ['admin', 'user', 'root'],
            ['password', 'pass', 'secret']
        ]

        result = weaver.filter_passwords(candidates, 1, 100, word_groups)

        self.assertNotIn('adminuserroot', result)

        self.assertIn('adminsecret', result)

    def test_pattern_with_static_text(self):
        """Test patterns that mix placeholders with static text."""
        patterns = ["prefix_{word1}_suffix", "test{number}end"]
        words = ['admin']
        numbers = ['123']
        specials = ['!']

        result = weaver.generate_passwords(patterns, words, numbers, specials)

        self.assertIn('prefix_admin_suffix', result)
        self.assertIn('test123end', result)

    def test_multiple_same_placeholder_types(self):
        """Test patterns with multiple placeholders of same type."""
        patterns = ["{word1}{word2}{word3}"]
        words = ['a', 'b', 'c', 'd']
        numbers = []
        specials = []

        result = weaver.generate_passwords(patterns, words, numbers, specials)

        self.assertIn('abc', result)
        self.assertIn('bcd', result)
        self.assertNotIn('aaa', result)

    def test_special_characters_various_formats(self):
        """Test various special character input formats."""

        specials1 = list('!@#')
        specials2 = ['!', '@', '#']

        patterns = ["{special}"]
        result1 = weaver.generate_passwords(patterns, ['test'], [], specials1)
        result2 = weaver.generate_passwords(patterns, ['test'], [], specials2)

        self.assertEqual(result1, result2)

    def test_case_sensitivity_preservation(self):
        """Test that case is preserved correctly in different contexts."""
        patterns = ["{word1}", "{WORD1}", "{Word1}"]
        words = ['TeSt']

        result = weaver.generate_passwords(patterns, words, [], [])

        self.assertIn('test', result)
        self.assertIn('TEST', result)
        self.assertIn('Test', result)

    def test_empty_pattern_list(self):
        """Test behavior with empty pattern list."""
        result = weaver.generate_passwords([], ['admin'], ['123'], ['!'])
        self.assertEqual(result, set())

    def test_whitespace_in_inputs(self):
        """Test handling of whitespace in various inputs."""

        words_with_space = ['hello world', 'test space']
        patterns = ["{word1}"]

        result = weaver.generate_passwords(patterns, words_with_space, [], [])

        self.assertIn('hello world', result)
        self.assertIn('test space', result)


class TestPerformanceAndScalability(unittest.TestCase):
    """Test performance and scalability aspects."""

    def test_large_combination_generation(self):
        """Test generating large numbers of combinations."""
        patterns = ["{word1}{number}{special}"]
        words = [f'word{i}' for i in range(10)]
        numbers = [f'{i}' for i in range(10)]
        specials = [chr(33 + i) for i in range(10)]

        result = weaver.generate_passwords(patterns, words, numbers, specials)

        self.assertTrue(len(result) <= 1000)
        self.assertTrue(len(result) > 0)

    def test_memory_efficiency_with_large_inputs(self):
        """Test memory efficiency with large inputs."""
        import sys

        large_words = [f'word{i}' for i in range(100)]
        patterns = ["{word1}"]

        result = weaver.generate_passwords(patterns, large_words, [], [])

        self.assertEqual(len(result), 100)

    def test_filtering_performance(self):
        """Test filtering performance with large candidate lists."""

        candidates = [f'password{i}' for i in range(1000)]
        word_groups = [['password', 'pass'], ['admin', 'user']]

        result = weaver.filter_passwords(candidates, 5, 20, word_groups)

        expected_length = [pw for pw in candidates if 5 <= len(pw) <= 20]
        self.assertTrue(len(result) <= len(expected_length))


if __name__ == '__main__':

    unittest.main(verbosity=2)
