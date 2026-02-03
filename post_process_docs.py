#!/usr/bin/env python3

import os
import re
import json

def rename_files(docs_dir='docs/api-reference/python'):
	"""
	1. Rename __init__.md files to init.md
	2. Remove leading underscores from filenames
	"""
	renamed_init_files = 0
	renamed_underscore_files = 0

	# Walk through the docs directory
	for root, _, files in os.walk(docs_dir):
		for file in files:
			# Rename __init__.md to init.md
			if file == "__init__.md":
				old_path = os.path.join(root, file)
				new_path = os.path.join(root, "init.md")
				os.rename(old_path, new_path)
				renamed_init_files += 1

			# Remove leading underscore from filenames
			elif file.startswith('_') and file != "__init__.md":
				old_path = os.path.join(root, file)
				new_path = os.path.join(root, file[1:])
				os.rename(old_path, new_path)
				renamed_underscore_files += 1

	print(f"Renamed {renamed_init_files} __init__.md files to init.md")
	print(f"Renamed {renamed_underscore_files} files by removing leading underscore")

def process_content(docs_dir='docs/api-reference/python'):
	"""
	Process markdown content:
	1. Escape braces outside code blocks
	"""
	modified_files = 0

	# Walk through the docs directory
	for root, _, files in os.walk(docs_dir):
		for file in files:
			if file.endswith('.md'):
				file_path = os.path.join(root, file)

				# Read the file
				with open(file_path, 'r') as f:
					content = f.read()

				# Process content
				original_content = content

				# Escape braces outside code blocks
				parts = re.split(r'(```.*?```)', content, flags=re.DOTALL)
				for i in range(len(parts)):
					if i % 2 == 0:  # Outside code blocks
						parts[i] = re.sub(r'(?<!\\)\{', r'\\{', parts[i])
				content = ''.join(parts)

				# Write back if modified
				if content != original_content:
					with open(file_path, 'w') as f:
						f.write(content)
					modified_files += 1

	print(f"Processed {modified_files} markdown files (escaped braces)")

def mark_empty_init_files(docs_dir='docs/api-reference/python'):
	"""
	Mark empty init.md files as drafts
	"""
	modified_files = 0

	# Walk through the docs directory
	for root, _, files in os.walk(docs_dir):
		for file in files:
			if file == 'init.md':
				file_path = os.path.join(root, file)

				# Check if the file is empty
				with open(file_path, 'r') as f:
					content = f.read()

				# Remove frontmatter
				frontmatter_pattern = re.compile(r'^---\n.*?---\n', re.DOTALL)
				content_without_frontmatter = frontmatter_pattern.sub('', content).strip()

				# If empty, add draft: true to frontmatter
				if len(content_without_frontmatter) == 0 or content_without_frontmatter.isspace():
					modified_content = re.sub(
						r'^(---\n)', r'\1draft: true\n', 
						content, 
						count=1, 
						flags=re.MULTILINE
					)

					with open(file_path, 'w') as f:
						f.write(modified_content)
					
					modified_files += 1

	print(f"Marked {modified_files} empty init files as drafts")

def configure_sidebar(sidebar_path='docs/api-reference/python/api_sidebar.js'):
	"""
	Configure sidebar:
	1. Fix sidebar references (__init__ -> init)
	2. Make top-level categories non-collapsible
	3. Add landing page link
	"""
	# Read the sidebar file
	with open(sidebar_path, 'r') as f:
		content = f.read()

	# 1. Fix sidebar references
	init_replacements = content.count('__init__')
	content = re.sub(r'/__init__"', r'/init"', content)

	# Write the intermediate changes
	with open(sidebar_path, 'w') as f:
		f.write(content)

	# Read as JSON for structural changes
	with open(sidebar_path, 'r') as f:
		sidebar_data = json.load(f)

	# 2. Make top-level categories non-collapsible
	sidebar_data["collapsible"] = False
	for item in sidebar_data.get("items", []):
		if isinstance(item, dict) and item.get("type") == "category":
			item["collapsible"] = False

	# 3. Add landing page link
	sidebar_data["link"] = {
		"type": "doc",
		"id": "api-reference/python/python"
	}

	# Write back the modified JSON
	with open(sidebar_path, 'w') as f:
		json.dump(sidebar_data, f, indent=2)

	print(f"Updated {init_replacements} __init__ references to init in sidebar")
	print(f"Added collapsible: false to top-level categories")
	print(f"Added landing page link to sidebar")

def main():
	"""
	Execute all post-processing steps for documentation
	"""
	print("Starting documentation post-processing...")

	# Create docs directory if it doesn't exist
	os.makedirs('docs/api-reference/python', exist_ok=True)

	# 1. Rename files
	rename_files()

	# 2. Process content
	process_content()

	# 3. Mark empty init files
	mark_empty_init_files()

	# 4. Configure sidebar
	configure_sidebar()

	print("Documentation post-processing complete!")

if __name__ == "__main__":
	main()
