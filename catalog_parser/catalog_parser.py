import requests
import re
import logging
from typing import List, Dict
from pathlib import Path
import json

from bs4 import BeautifulSoup

from course import Prerequisite

# Set up logging
logging.basicConfig(format='[%(levelname)s] [%(name)s] %(message)s', level=logging.DEBUG)
logging.getLogger().handlers[0].addFilter(lambda record: 'catalog_parser' in record.name or 'catalog_parser' in record.pathname)
logger = logging.getLogger(__name__)


class CatalogParser:

    def __init__(self):
        self._cache_dir = Path('..', 'cache', 'catalog')

    def get_courses(self) -> List[Dict[str, str]]:
        """
        Get a list of all courses.
        :return: A list of dictionaries containing course information. Each dictionary has the following format:
        {
            'department_code': str. Department code. (Ex. "COMPSCI")
            'number': str. Course number (Ex. "297P")
            'title': str. Course title (Ex. "Capstone Design Project for Computer Science")
            'units': Optional[str]. A string representing the number of units. This can be a single integer (Ex. "2") or floating point number (Ex. "7.5") OR a range of numbers
                    (Ex. "4-12"). Note that the number of units is not always present.
            'prerequisite':
            'corequisite':
            'restriction':
            'equivalent':
            'concurrent':
            'repeatability':
            'overlap':
            'grading_option':
        }
        """

        # Check if the catalog exists in the cache
        catalog_cache_path = (self._cache_dir / 'department_catalogs').with_suffix('.json')
        if catalog_cache_path.exists():
            with open(catalog_cache_path, 'r') as file:
                departments = json.load(file)
        else:
            departments = self._download_department_catalogs()
            with open(catalog_cache_path, 'w') as file:
                json.dump(departments, file)

        # Gather catalog HTML pages
        html_catalogs = [d['catalog_html'] for d in departments]

        # First pass: Parse basic course information
        courses = []
        for catalog_html in html_catalogs:

            # Clean content
            catalog_html = catalog_html.replace('&#160;', ' ')  # Non-breaking space

            soup = BeautifulSoup(catalog_html, 'lxml')
            courses_div = soup.find('div', attrs={'class': 'courses'})
            course_blocks = courses_div.find_all('div', attrs={'class': 'courseblock'})

            for block in course_blocks:
                paragraphs = block.find_all('p')

                # Parse department code, course number, and course title
                title_paragraph_text = paragraphs[0].text
                match = re.match(re.compile(r'^(.+?) (\S+?)\.  (.+?)\.  (.+)?$'), title_paragraph_text)
                if not match:
                    logging.warning(f'Failed to parse course title paragraph: {title_paragraph_text}')
                    continue
                department_code = match.group(1)
                course_number = match.group(2)
                course_title = match.group(3)
                units_string = match.group(4)

                course = {
                    'department_code': department_code,
                    'number': course_number,
                    'title': course_title
                }

                # Parse units
                if units_string is not None:
                    match = re.match(r'^\.?(\d+(?:\.\d+)?(?:(?:\s*-\s*|\.)\d+)?) Units?\.  $', units_string)
                    if match:
                        course['units'] = match.group(1)
                    else:
                        logging.warning(f'Failed to parse units string: "{units_string}"')
                else:
                    logging.warning(f'No units found in title paragraph: "{title_paragraph_text}"')

                # Description
                course['description'] = paragraphs[1].text

                # Save remaining paragraphs (they will be parsed on the second pass)
                course['paragraphs'] = paragraphs[2:]

                courses.append(course)

        # Second pass: Parse extra paragraphs (prerequisites, restrictions, etc.)
        valid_courses = [' '.join([c['department_code'], c['number']]) for c in courses]
        for course in courses:
            for paragraph in course['paragraphs']:

                # Prerequisites
                match = re.match(r'^Prerequisite:\s*(.+)$', paragraph.text)
                if match:
                    try:
                        course['prerequisite'] = parse_prerequisite(match.group(1), valid_courses)
                    except Exception as e:
                        # logger.error(f'Failed to parse prerequisites for {course["department_code"]} {course["number"]}!', exc_info=e)
                        pass
                    continue

                # Corequisite
                match = re.match(r'^Corequisite: (.+)$', paragraph.text)  # TODO: validate course codes and parse
                if match:
                    course['corequisite'] = match.group(1)
                    continue

                # Restrictions
                match = re.match(r'^Restriction:\s*(.+)$', paragraph.text)
                if match:
                    course['restriction'] = match.group(1)
                    continue

                # Same
                match = re.match(r'^Same as (.+)\.$', paragraph.text)
                if match:
                    course['equivalent'] = match.group(1)  # TODO: Validate course codes
                    continue

                # Concurrent
                match = re.match(r'^Concurrent with (.+)\.$', paragraph.text)
                if match:
                    course['concurrent'] = match.group(1)  # TODO: Validate course codes and parse multiple
                    continue

                # Repeatability
                match = re.match(r'^Repeatability:\s*(.+)$', paragraph.text)  # TODO: parse number?
                if match:
                    course['repeatability'] = match.group(1)
                    continue

                # Overlaps
                match = re.match(r'^Overlaps with (.+)\.$', paragraph.text)  # TODO: validate course codes and parse
                if match:
                    course['overlap'] = match.group(1)
                    continue

                # Grading Option
                match = re.match(r'^Grading Option: (.+)$', paragraph.text)
                if match:
                    course['grading_option'] = match.group(1)
                    continue

                logger.warning(f'Unrecognized paragraph: {bytes(paragraph.text, encoding="utf-8")}')

        return courses

    def _download_department_catalogs(self):
        # Create directory
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        root_url = 'http://catalogue.uci.edu/allcourses/'
        response = requests.get(root_url)

        soup = BeautifulSoup(response.content, 'lxml')
        a_to_z_index = soup.find('div', attrs={'id': 'atozindex'})
        department_urls = a_to_z_index.find_all('a', href=re.compile(r'/allcourses/.+/'))

        departments = []
        for url in department_urls:
            match = re.match(re.compile(r'^(.+) \((.+)\)$'), url.text)

            department_name = match.group(1)
            department_code = match.group(2)

            logger.info(f'Downloading catalog for department: {department_code}')

            response = requests.get(root_url + url['href'].split('/')[2])
            catalog_html = response.text

            logger.info(f'Downloaded {len(response.content)} bytes.')

            departments.append({
                'catalog_html': catalog_html,
                'name': department_name,
                'code': department_code
            })

        return departments


def tokenize_prerequisite_string(prerequisite_string: str, valid_courses: [str]):
    # Add spaces around parenthesis so we can split the input on spaces
    prerequisite_string = prerequisite_string.replace('(', ' ( ')
    prerequisite_string = prerequisite_string.replace(')', ' ) ')

    # Tokenize input
    tokens = []
    items = []

    def maybe_add_course():
        data = ' '.join(items).strip()
        if len(data) > 0:

            if data not in valid_courses:
                raise RuntimeError('Invalid course:', data)

            tokens.append(data)
            items.clear()

    for item in prerequisite_string.split():

        # Ignore empty items
        if len(item) == 0:
            continue

        if item == '(' or item == ')' or item == 'or' or item == 'and':
            maybe_add_course()
            tokens.append(item)
            continue

        items.append(item)

    maybe_add_course()

    return tokens


def parse_prerequisite_courses(string: str, valid_courses):

    #print('PRE:', string)

    tokens = tokenize_prerequisite_string(string, valid_courses)
    #print(tokens)

    # A or (B and C) or (E and F)

    stack = [[None, []]]
    for token in tokens:
        if token == '(':
            stack.append([None, []])
        elif token == ')':
            stack[-2][1].append(stack.pop())
        elif token == 'or':
            if stack[-1][0] is None:
                stack[-1][0] = 'or'
            if stack[-1][0] != 'or':
                raise RuntimeError('Parsing error: Ambiguous operator!')
        elif token == 'and':
            if stack[-1][0] is None:
                stack[-1][0] = 'and'
            if stack[-1][0] != 'and':
                raise RuntimeError('Parsing error: Ambiguous operator!')
        else:
            stack[-1][1].append(token)

    return stack[-1]


def parse_prerequisite(prerequisite_string: str, valid_courses) -> [Prerequisite]:

    # Split into statements
    statements = [x for x in prerequisite_string.split('.') if len(x) > 0]

    # Parse the first statement. This contains the prerequisite courses
    result = parse_prerequisite_courses(statements[0], valid_courses)

    return result


if __name__ == '__main__':

    parser = CatalogParser()
    courses = parser.get_courses()

    for c in courses:
        if c['department_code'] == 'COMPSCI':
            if 'prerequisite' in c:
                print(c['prerequisite'])
