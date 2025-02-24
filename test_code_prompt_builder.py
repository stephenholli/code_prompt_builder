import os
import json
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock
from code_prompt_builder import load_or_create_settings, build_code_prompt

class TestCodePromptBuilder(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        self.sample_files = {
            "src/index.html": "<html><body>Hello</body></html>",
            "src/script.js": "function test() { console.log('test'); }",
            "code_prompt_builder.py": "print('self')",
            "README.md": "# Test README",
            "ignored.min.js": "minified content",
            "other.txt": "not included"
        }
        for filepath, content in self.sample_files.items():
            os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

    def tearDown(self):
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)

    def read_output_file(self, output_dir="."):
        for f in os.listdir(output_dir):
            if f.endswith(".txt"):
                with open(os.path.join(output_dir, f), 'r', encoding='utf-8') as infile:
                    return infile.read()
        return None

    def test_load_or_create_settings_default(self):
        settings = load_or_create_settings()
        self.assertEqual(settings["extensions"], [".html", ".css", ".js", ".py", ".md"])
        self.assertEqual(settings["exclude_files"], ["code_prompt_builder.py"])
        self.assertTrue(os.path.exists("code_prompt_builder_config.json"))

    def test_load_or_create_settings_custom(self):
        custom_settings = {
            "extensions": [".html", ".txt"],
            "exclude_files": ["test.py"]
        }
        with open("code_prompt_builder_config.json", 'w', encoding='utf-8') as f:
            json.dump(custom_settings, f)
        settings = load_or_create_settings()
        self.assertEqual(settings["extensions"], [".html", ".txt"])
        self.assertEqual(settings["exclude_files"], ["test.py"])

    @patch('sys.stdout', new_callable=MagicMock)
    def test_normal_mode_default(self, mock_stdout):
        build_code_prompt()
        output = self.read_output_file()
        
        self.assertIsNotNone(output)
        self.assertIn("Code Export", output)
        self.assertIn(f"[HTML] {os.path.basename(self.temp_dir)}\\src\\index.html", output)
        self.assertIn(f"[JAVASCRIPT] {os.path.basename(self.temp_dir)}\\src\\script.js", output)
        self.assertIn(f"[PYTHON] {os.path.basename(self.temp_dir)}\\code_prompt_builder.py", output)
        self.assertIn(f"[MARKDOWN] {os.path.basename(self.temp_dir)}\\README.md", output)
        self.assertNotIn("ignored.min.js", output)
        self.assertNotIn("other.txt", output)
        self.assertIn("Files: 4", output)

    @patch('sys.stdout', new_callable=MagicMock)
    def test_self_run_mode(self, mock_stdout):
        build_code_prompt(self_run=True)
        output = self.read_output_file()
        
        self.assertIsNotNone(output)
        self.assertIn("Code Export", output)
        self.assertIn(f"[PYTHON] {os.path.basename(self.temp_dir)}\\code_prompt_builder.py", output)
        self.assertIn(f"[MARKDOWN] {os.path.basename(self.temp_dir)}\\README.md", output)
        self.assertNotIn("src\\index.html", output)
        self.assertNotIn("src\\script.js", output)
        self.assertIn("Files: 2", output)
        mock_stdout.write.assert_called_with(f"Done! Self-run output written to '{os.path.join('.', os.path.basename(self.temp_dir) + '-code-prompt-' + datetime.now().strftime('%Y-%m-%d_%H%M') + '.txt')}' if no errors occurred.\n")

    @patch('sys.stdout', new_callable=MagicMock)
    def test_target_dir(self, mock_stdout):
        target_subdir = os.path.join(self.temp_dir, "src")
        build_code_prompt(target_dir=target_subdir)
        output = self.read_output_file()
        
        self.assertIsNotNone(output)
        self.assertIn("src Code Export", output)
        self.assertIn("[HTML] src\\index.html", output)
        self.assertIn("[JAVASCRIPT] src\\script.js", output)
        self.assertNotIn("code_prompt_builder.py", output)
        self.assertNotIn("README.md", output)
        self.assertIn("Files: 2", output)

    @patch('sys.stdout', new_callable=MagicMock)
    def test_output_dir(self, mock_stdout):
        output_subdir = os.path.join(self.temp_dir, "output")
        build_code_prompt(output_dir=output_subdir)
        output = self.read_output_file(output_subdir)
        
        self.assertIsNotNone(output)
        self.assertIn("Code Export", output)
        self.assertIn(f"[HTML] {os.path.basename(self.temp_dir)}\\src\\index.html", output)
        self.assertIn("Files: 4", output)
        self.assertTrue(os.path.exists(output_subdir))

    @patch('os.path.sep', '/')
    def test_linux_path_handling(self):
        build_code_prompt()
        output = self.read_output_file()
        
        self.assertIn(f"[HTML] {os.path.basename(self.temp_dir)}/src/index.html", output)
        self.assertIn(f"[JAVASCRIPT] {os.path.basename(self.temp_dir)}/src/script.js", output)

    @patch('os.path.sep', '\\')
    def test_windows_path_handling(self):
        build_code_prompt()
        output = self.read_output_file()
        
        self.assertIn(f"[HTML] {os.path.basename(self.temp_dir)}\\src\\index.html", output)
        self.assertIn(f"[JAVASCRIPT] {os.path.basename(self.temp_dir)}\\src\\script.js", output)

    @patch('builtins.open', side_effect=PermissionError)
    @patch('sys.stdout', new_callable=MagicMock)
    def test_permission_error(self, mock_stdout, mock_open):
        build_code_prompt()
        mock_stdout.write.assert_any_call(f"Error: No permission to write '{os.path.join('.', os.path.basename(self.temp_dir) + '-code-prompt-' + datetime.now().strftime('%Y-%m-%d_%H%M') + '.txt')}'. Aborting.\n")

    @patch('json.load', side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
    @patch('sys.stdout', new_callable=MagicMock)
    def test_invalid_config(self, mock_stdout, mock_json):
        with open("code_prompt_builder_config.json", 'w', encoding='utf-8') as f:
            f.write("invalid json")
        settings = load_or_create_settings()
        self.assertEqual(settings["extensions"], [".html", ".css", ".js", ".py", ".md"])
        mock_stdout.write.assert_any_call("Error: 'code_prompt_builder_config.json' is corrupted or invalid JSON. Using defaults.\n")

if __name__ == "__main__":
    unittest.main()