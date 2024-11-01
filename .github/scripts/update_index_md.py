#!/usr/bin/env python

import os
import sys
import json
from collections import OrderedDict

'''
This script requires following environment variables:

- REPO_NAME:
  > example: 'iamwatchdogs/test'
  > GitHub action variable: ${{ github.repository }}
'''

class UpdateFileContent:
	"""Class that updates `index.md` based on contributors-log."""

	# Setting static variables
	DATA = None
	REPO_NAME = None

	def __init__(self, FILE_PATH, condition=None):
		"""
		Initializes required variables and updates target file based on data.

		Updates the file located at `FILE_PATH` with contributor and content
		tables. If `condition` is not `None`, it will be used to filter out
		core contributions when updating the content table.

		:arg FILE_PATH: Path to the file to be updated.
		:arg condition: Optional condition to filter out core contributions.
		"""

		# Displaying starting Message
		print(f'\n--- Updating {FILE_PATH} ---\n')

		# Setting Constant values
		self.FILE_PATH = FILE_PATH

		# Retriving data as modifiable lines
		self.lines = self.get_lines()

		# Updates lines based on the data
		self.update_table_of_contributors(condition)
		self.update_table_of_content(condition)

		# Updating target file content
		self.write_lines_into_file()


	def get_lines(self):
		"""
		Reads lines from the file located at `self.FILE_PATH` and returns them.
		
		:return: List of lines read from the file.
		"""

		# Reading lines from the file
		with open(self.FILE_PATH, 'r') as file:
			lines = file.readlines()

		return lines

	def write_lines_into_file(self):
		"""
		Writes the lines in `self.lines` to the file located at `self.FILE_PATH`
		and prints a success message.

		:return: None
		"""

		# Updating the target file
		with open(self.FILE_PATH, 'w') as file:
			file.writelines(self.lines)

		# Printing Success Message
		print(f"Updated '{self.FILE_PATH}' Successfully")

	def find_table_points(self, search_type):
		"""
		Finds the starting and ending points of a table in the file located at
		`self.FILE_PATH` based on the `search_type`.

		:arg search_type: Type of table to search for. Valid values are
			`contributors` and `table-of-content`.
		:return: A tuple of `(table_starting_point, table_ending_point)` where
			`table_starting_point` is the index of the line where the table
			starts and `table_ending_point` is the index of the line where the
			table ends.
		"""

		# Setting default return values
		table_starting_point = None
		table_ending_point = None

		# Setting default markers
		table_start_marker = None
		table_end_marker = None

		# Selecting respective markers based on `search-type`
		if search_type == 'contributors':
			table_start_marker = '<!-- TABLE OF CONTRIBUTORS BEGINS -->'
			table_end_marker= '<!-- TABLE OF CONTRIBUTORS ENDS -->'
		elif search_type == 'table-of-content':
			table_start_marker = '<!-- TABLE OF CONTENT BEGINS -->'
			table_end_marker= '<!-- TABLE OF CONTENT ENDS -->'
		else:
			print('Invalid Argument', file=sys.stderr)
			exit(1)

		# Iterating over lines to find the markers
		for index, line in enumerate(self.lines):
			if table_starting_point is None and table_start_marker in line:
				table_starting_point = index
			elif table_ending_point is None and table_end_marker in line:
				table_ending_point = index
			if table_starting_point is not None and table_ending_point is not None:
				break

		# Checking for possible errors
		if table_starting_point is None or table_ending_point is None:
			print('Table not found in the file.', file=sys.stderr)
			exit(2)
		elif table_starting_point >= table_ending_point:
			print('Invaild use of table markers.', file=sys.stderr)
			exit(3)

		return (table_starting_point, table_ending_point)

	def update_table_of_contributors(self, condition):
		"""
		Update the table of contributors based on the condition.

		Args:
			condition (callable): A function that takes one argument (i.e., the core contribution)
				and returns True if the contribution should be included in the table, or
				False otherwise. If None, then all core contributions are included.
		"""

		# Calculating stating and ending points of the targeted table
		table_of_contributors_start, table_of_contributors_end = self.find_table_points('contributors')

		# Creating table header if doesn't exist
		if table_of_contributors_end - table_of_contributors_start == 1:
			table_header = list()
			if condition is None:
				table_header.append('| Contribution Title | Core Contribution | Contributor Names | Pull Requests | Demo |\n')
				table_header.append('| --- | --- | --- | --- | --- |\n')
			else:
				table_header.append('| Contribution Title | Contributor Names | Pull Requests | Demo |\n')
				table_header.append('| --- | --- | --- | --- |\n')
			self.lines[table_of_contributors_start+1:table_of_contributors_end] = table_header

		# Initializing empty list for lines
		updated_lines = list()

		# Checking for min entries
		has_at_least_one_entry = False

		# Iterating over log to update target file
		for title, details in self.DATA.items():

			# Modifying based on condition
			if condition is not None and not condition(details['core']):
				continue

			# Processing contributors-names
			contributors_names = details['contributor-name']
			contributors_names_list = [f'[{name}](https://github.com/{name} "goto {name} profile")' for name in contributors_names]
			contributors_names_output = ', '.join(contributors_names_list)

			# Processing core contribution
			core_contribution = details['core']
			if condition is None:
				core_contribution_output = f'[{core_contribution}]({core_contribution} "goto {core_contribution}")' if core_contribution != 'Repo' else 'Repo'

			# Processing pull-requests
			pull_requests = details['pull-request-number']
			pull_requests_list = [f'[#{pr}](https://github.com/{self.REPO_NAME}/pull/{pr} "visit pr \#{pr}")' for pr in pull_requests]
			pull_requests_output = ', '.join(pull_requests_list)

			# Processing demo-path
			demo_path = details['demo-path']
			specificity = details['specificity']
			if ' ' in demo_path:
				demo_path = '%20'.join(demo_path.split())
			demo_path_output = f'[./{core_contribution}/{specificity}/]({demo_path} "view the result of {title}")'
			if title == 'root' or title == '{init}':
				demo_path_output = f'[/{self.REPO_NAME}/]({demo_path} "view the result of {title}")'
			elif title == '{workflows}':
				demo_path_output = f'[/{self.REPO_NAME}/.github/workflows]({demo_path} "view the result of {title}")'
			elif title == '{scripts}':
				demo_path_output = f'[/{self.REPO_NAME}/.github/scripts]({demo_path} "view the result of {title}")'
			elif title == '{others}':
				demo_path_output = f'[/{self.REPO_NAME}/.github]({demo_path} "view the result of {title}")'

			# Appending all data together
			if condition is None:
				updated_lines.append(f'| {title} | {core_contribution_output} | {contributors_names_output} | {pull_requests_output} | {demo_path_output} |\n')
			else:
				updated_lines.append(f'| {title} | {contributors_names_output} | {pull_requests_output} | {demo_path_output} |\n')

			has_at_least_one_entry = True

		# Adding null entries for completely empty table
		if not has_at_least_one_entry:
			if condition is None:
				updated_lines.append('| - | - | - | - | - |\n')
			else:
				updated_lines.append('| - | - | - | - |\n')

		# Updating the lines with updated data
		self.lines[table_of_contributors_start+3:table_of_contributors_end] = updated_lines

		# Printing Success Message
		print('Successfully updated the contributor details !!!...')

	def update_table_of_content(self, condition):
		"""
		Update the table of content based on the specified condition.

		Args:
				condition (callable): A function that takes one argument (i.e., the core contribution)
						and returns True if the contribution should be included in the table, or
						False otherwise. If None, then all core contributions are included.
		"""

		# Calculating stating and ending points of the targeted table
		table_of_content_start, table_of_content_end = self.find_table_points('table-of-content')

		# Initializing required variables
		updated_lines = list()
		table_of_content = { 'Theory': {}, 'Solved-Problems': {}, 'Repo': {} }

		# Extracting data into required format
		for title, data in self.DATA.items():

			# Setting values for ease of use and more readibility
			core = data['core']
			specificity = data['specificity']

			# Sorting out required data
			if specificity not in table_of_content[core]:
				table_of_content[core][specificity] = None if specificity == title else [title]
			elif title != specificity and title not in table_of_content[core][specificity]:
				if table_of_content[core][specificity] is None:
					table_of_content[core][specificity] = [title]
				else:
					table_of_content[core][specificity].append(title)

		# Sorting extracted data
		for key, value in table_of_content.items():
			for sub_value in value.values():
				if type(sub_value) == list:
					sub_value.sort()
			table_of_content[key] = OrderedDict(sorted(value.items()))

		# Updating lines based on the extracted data
		for core, data in table_of_content.items():

			# Modifying based on condition
			if condition is not None and not condition(core) or core == 'Repo':
				continue

			# Setting Main Heading (Only for Root)
			if condition is None:
				updated_lines.append(f'- [__{core}__]({core} "goto {core}")\n')

			# Adding all headings
			for  heading, sub_heading_list in data.items():
				if condition is None:
					updated_lines.append(f'\t- [{heading}]({core}/{heading} "goto {heading}")\n')
				else:
					updated_lines.append(f'- [__{heading}__]({heading} "goto {heading}")\n')
				if sub_heading_list is not None:
					for sub_heading in sub_heading_list:
						if condition is None:
							updated_lines.append(f'\t\t- [{sub_heading}]({core}/{heading}/{sub_heading} "goto {sub_heading}")\n')
						else:
							updated_lines.append(f'\t- [{sub_heading}]({heading}/{sub_heading} "goto {sub_heading}")\n')

		# Updating the lines with updated data
		self.lines[table_of_content_start+1:table_of_content_end] = updated_lines

		# Printing Success Message
		print('Successfully updated the table of content !!!...')


def main():
	"""
	The main function of the script is responsible for updating the root index file and the index files of `Theory` and `Solved-Problems` directories.

	The function takes in environment variables `REPO_NAME` and uses it to fetch the required data from the contributors log file.

	The function then updates the root index file and the index files of `Theory` and `Solved-Problems` directories using the fetched data.

	The function also prints out a success message at the end.
	"""

	# Retrieving Environmental variables
	REPO_NAME = os.environ.get('REPO_NAME')

	# Setting path for the log JSON file
	ROOT_INDEX_FILE_PATH = 'index.md'
	THEORY_INDEX_FILE_PATH = 'Theory/index.md'
	THEORY_README_FILE_PATH = 'Theory/README.md'
	SOLVED_PROBLEM_INDEX_FILE_PATH = 'Solved-Problems/index.md'
	SOLVED_PROBLEM_README_FILE_PATH = 'Solved-Problems/README.md'
	CONTRIBUTORS_LOG = '.github/data/contributors-log.json'

	# Retrieving data from log file
	with open(CONTRIBUTORS_LOG, 'r') as json_file:
		DATA = json.load(json_file)

	# Assigning values to static members for class `UpdateFileContent`
	UpdateFileContent.DATA = DATA
	UpdateFileContent.REPO_NAME = REPO_NAME

	# Updating All required files
	UpdateFileContent(ROOT_INDEX_FILE_PATH)
	UpdateFileContent(THEORY_INDEX_FILE_PATH, lambda core: core == 'Theory')
	UpdateFileContent(THEORY_README_FILE_PATH, lambda core: core == 'Theory')
	UpdateFileContent(SOLVED_PROBLEM_INDEX_FILE_PATH, lambda core: core == 'Solved-Problems')
	UpdateFileContent(SOLVED_PROBLEM_README_FILE_PATH, lambda core: core == 'Solved-Problems')

if __name__ == '__main__':
	main()
