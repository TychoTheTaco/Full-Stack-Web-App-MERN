import requests
import re
import logging
from typing import List, Dict, Union
from pathlib import Path
import json

from bs4 import BeautifulSoup

from tree_parser import TreeParser

# Set up logging
logging.basicConfig(format='[%(levelname)s] [%(name)s] %(message)s', level=logging.DEBUG)
logging.getLogger().handlers[0].addFilter(lambda record: 'catalog_parser' in record.name or 'catalog_parser' in record.pathname)
logger = logging.getLogger(__name__)


class CatalogParser:
    """
    http://catalogue.uci.edu/about/about.pdf
    """

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

            # The remaining items are not guaranteed to exist for every course!

            'units': Optional[str].A string representing the number of units. This can be a single integer (Ex. "2") or floating point
            number (Ex. "7.5") OR a range of numbers (Ex. "4-12").
            'workload_units': str. A string representing the number of units. This can be a single integer (Ex. "2") or floating point
            number (Ex. "7.5") OR a range of numbers (Ex. "4-12").
            'prerequisite_courses': A string or a list. If its a string, its a course ID (department + course number). If its a list, the
            first element is a string: either 'or' or 'and'. The second element is another list, which can hold either strings or more lists.
            'prerequisite_notes': str. If a course has prerequisites that could not be parsed into a tree, the raw string will end up here.
            'corequisite_courses': A string or a list. If its a string, its a course ID (department + course number). If its a list, the
            first element is a string: either 'or' or 'and'. The second element is another list, which can hold either strings or more lists.
            'corequisite_notes': str. If a course has corequisites that could not be parsed into a tree, the raw string will end up here.
            'prerequisite_or_corequisite_courses': A string or a list. If its a string, its a course ID (department + course number). If its a list, the
            first element is a string: either 'or' or 'and'. The second element is another list, which can hold either strings or more lists.
            'prerequisite_or_corequisite_notes': str. If a course has "prerequisites or corequisites" that could not be parsed into a tree, the raw string will end up here.
            'restriction': str.
            'equivalent': A list of course IDs that are equivalent to this course. ("Same as ..." in the catalog)
            'concurrent': str.
            'repeatability': str.
            'overlap': str.
            'grading_option': str.
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
                    self._parse_units_string(course, units_string)
                else:
                    logging.warning(f'No units found in title paragraph: "{title_paragraph_text}"')

                # Description
                course['description'] = paragraphs[1].text

                # Save remaining paragraphs (they will be parsed on the second pass)
                p = []
                for paragraph in paragraphs[2:]:
                    lines = paragraph.text.splitlines()
                    p.extend(lines)
                course['_paragraphs'] = p

                courses.append(course)

        valid_courses = {d['code']: [c['number'] for c in courses if c['department_code'] == d['code']] for d in departments}

        # Second pass: Parse extra paragraphs (prerequisites, restrictions, etc.)
        for course in courses:
            for paragraph in course['_paragraphs']:

                # Prerequisites
                match = re.match(r'^Prerequisite:\s*(.+)$', paragraph)
                if match:
                    self._parse_prerequisite_string(course, match.group(1), valid_courses=valid_courses)
                    continue

                # Corequisite
                match = re.match(r'^Corequisite: (.+)$', paragraph)
                if match:
                    self._parse_corequisite_string(course, match.group(1), valid_courses=valid_courses)
                    continue

                # Prerequisite OR Corequisite
                match = re.match(r'^Prerequisite or corequisite: (.+)$', paragraph)
                if match:
                    self._parse_prerequisite_or_corequisite_string(course, match.group(1), valid_courses=valid_courses)
                    continue

                # Restrictions
                match = re.match(r'^Restriction:\s*(.+)$', paragraph)  # TODO: Parse?
                if match:
                    course['restriction'] = match.group(1)
                    continue

                # Same
                match = re.match(r'^Same as (.+)\.$', paragraph)
                if match:
                    self._parse_same_as_string(course, match.group(1))  # TODO: Validate course codes?
                    continue

                # Concurrent
                match = re.match(r'^Concurrent with (.+)\.$', paragraph)
                if match:
                    course['concurrent'] = match.group(1)  # TODO: Validate course codes and parse multiple
                    continue

                # Repeatability
                match = re.match(r'^Repeatability:\s*(.+)$', paragraph)  # TODO: parse number?
                if match:
                    course['repeatability'] = match.group(1)
                    continue

                # Overlaps
                match = re.match(r'^Overlaps with (.+)\.$', paragraph)  # TODO: validate course codes and parse
                if match:
                    course['overlap'] = match.group(1)
                    continue

                # Grading Option
                match = re.match(r'^Grading Option: (.+)$', paragraph)  # TODO: Parse?
                if match:
                    course['grading_option'] = match.group(1)
                    continue

                # Design units
                match = re.match(r'^\(Design units: ((?:\d+\.\d+|\.\d+|\d+)(?:\s*-\s*(?:\d+\.\d+|\.\d+|\d+))?)\)', paragraph)
                if match:
                    course['design_units'] = match.group(1)
                    continue

                # GE Category
                match = re.match(r'^\((.+)\)\.?$', paragraph)
                if match:
                    try:
                        self._parse_ge_category_string(course, match.group(1))
                        continue
                    except Exception as e:
                        logger.warning(f'Failed to parse potential GE category for {course["department_code"]} {course["number"]}: {e}')

                logger.warning(f'Unrecognized paragraph for course {course["department_code"]} {course["number"]}: "{paragraph}"')
            del course['_paragraphs']

        # names = [course['department_code'] + ' ' + course['number'] for course in courses]
        # print(names)
        #
        # # Extras
        # for course in courses:
        #     if course['number'].upper().endswith('L'):
        #         non = course['department_code'] + ' ' + course['number'][:-1]
        #         if non in names:
        #             print('POTENTIAL LAB:', course['department_code'] + ' ' + course['number'])
        #         else:
        #             print('BAMBOOZLE:', course['department_code'] + ' ' + course['number'], 'NON:', non)

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

    @staticmethod
    def _parse_units_string(course, string: str):
        # Normal units
        match = re.match(r'^((?:\d+\.\d+|\.\d+|\d+)(?:\s*-\s*(?:\d+\.\d+|\.\d+|\d+))?) Units?', string)
        if match:
            course['units'] = match.group(1)

        # Workload units
        match = re.match(r'^((?:\d+\.\d+|\.\d+|\d+)(?:\s*-\s*(?:\d+\.\d+|\.\d+|\d+))?) Workload Units?', string)
        if match:
            course['workload_units'] = match.group(1)

        if 'units' not in course and 'workload_units' not in course:
            logging.warning(f'Failed to parse units string for {course["department_code"]} {course["number"]}! Units string: "{string}"')

    @staticmethod
    def _parse_prerequisite_string(course, string: str, valid_courses=None):
        string = string.strip()

        # Placement into ...
        if re.match(r'^Placement into (.+)', string):  # TODO: Parse course
            course['prerequisite_notes'] = string
            return

        # Parse some non-course prerequisites. (Not complete)
        if any([
            re.match(r'^Prerequisites vary\.$', string),
            re.match(r'^Audition required\.$', string),
            re.match(r'^Satisfactory completion of the lower-division writing requirement\.$', string, re.IGNORECASE),
            re.match(r'^Satisfaction of the UC Entry Level Writing requirement\.$', string),
            re.match(r'^Advancement to candidacy\.$', string)
        ]):
            course['prerequisite_notes'] = string
            return

        # Split into sentences
        sentences = split_sentences(string)

        # Parse the first sentences. This contains the prerequisite courses.
        try:
            course['prerequisite_courses'] = parse_prerequisite_courses(sentences[0], valid_courses=valid_courses)
        except Exception as e:
            logger.warning(
                f'Failed to parse prerequisites for {course["department_code"]} {course["number"]}! '
                f'Exception: "{e}" '
                f'Prerequisite string: "{string}"')
            course['prerequisite_notes'] = string
            return

        # TODO: Parse other sentences (grade requirements, etc.)
        notes = ' '.join(sentences[1:])
        if len(notes) > 0:
            course['prerequisite_notes'] = notes

    @staticmethod
    def _parse_same_as_string(course, string: str) -> [str]:
        course_ids = string.split(',')
        course_ids = [x.strip() for x in course_ids]
        course['equivalent'] = course_ids

    @staticmethod
    def _parse_ge_category_string(course, string: str):
        string = string.strip()

        tree_parser = TreeParser('(', ')', ('and', 'or'))
        tokens = tree_parser.tokenize(string)

        # (https://www.reg.uci.edu/help/WebSoc-Glossary.shtml)
        GE_CATEGORIES = [
            'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'Ia', 'Ib', 'Va', 'Vb'
        ]

        for token in tokens:
            if token not in GE_CATEGORIES + ['(', ')', 'and', 'or', 'VA', 'V.A.', 'Va.', 'VB', 'V.B', 'IB']:
                raise RuntimeError('Invalid GE')

        course['ge_category'] = string  # TODO: Parse into tree?

    @staticmethod
    def _parse_corequisite_string(course, string: str, valid_courses=None) -> None:

        # Remove trailing period
        if string.endswith('.'):
            string = string[:-1]

        # Ignore empty string
        if len(string.strip()) == 0:
            return

        # Try to parse the course tree
        try:
            course['corequisite_courses'] = parse_prerequisite_courses(string, valid_courses=valid_courses)
        except Exception as e:
            logger.warning(
                f'Failed to parse corequisite for {course["department_code"]} {course["number"]}! '
                f'Exception: "{e}" '
                f'Corequisite string: "{string}"')
            course['corequisite_notes'] = string
            return

    @staticmethod
    def _parse_prerequisite_or_corequisite_string(course, string: str, valid_courses=None) -> None:

        # Remove trailing period
        if string.endswith('.'):
            string = string[:-1]

        # Ignore empty string
        if len(string.strip()) == 0:
            return

        # Split into sentences
        sentences = split_sentences(string)

        # Parse the first sentences. This contains the course tree.
        try:
            course['prerequisite_or_corequisite_courses'] = parse_prerequisite_courses(sentences[0], valid_courses=valid_courses)
        except Exception as e:
            logger.warning(
                f'Failed to parse prerequisite or corequisite for {course["department_code"]} {course["number"]}! '
                f'Exception: "{e}" '
                f'String: "{string}"')
            course['prerequisite_or_corequisite_notes'] = string
            return

        # TODO: Parse other sentences (grade requirements, etc.)
        notes = ' '.join(sentences[1:])
        if len(notes) > 0:
            course['prerequisite_or_corequisite_notes'] = notes


def parse_prerequisite_courses(string: str, valid_courses=None):
    """
    Parse a list of tokens to a tree of prerequisites.
    :param string:
    :return:
    """

    # Rename some department codes (Ex. PHYS -> PHYSICS)
    department_remap = {
        'PHYS': 'PHYSICS',
        'PSYC': 'PSYCH',
        'PUBH': 'PUBHLTH',
        'STAT': 'STATS',
        'SE': 'SOCECOL',
        'SSCI': 'SOC SCI',
        'ICS': 'I&C SCI',
        'MAE': 'ENGRMAE',
        'CEMS': 'CBE',
        'CEE': 'ENGRCEE',
        'ESS': 'EARTHSS',
        'PS': 'PHY SCI',
        'ENGRENGRCEE': 'ENGRCEE',
        'ANTH': 'ANTHRO',
        'CS': 'COMPSCI',
        'PHIL': 'PHILOS',
        'SPAN': 'SPANISH',
        'PSB': 'PSCI',
        'FREN': 'FRENCH',
        'ENGRMSE': 'MSE',
        'MMG': 'M&MG',
        'CLS': 'CRM/LAW',
        'SOCL': 'SOCIOL',
        'PPD': 'PP&D'
    }

    # These are department codes that are in the correct format and otherwise valid, but don't exist in the catalog anymore
    valid_but_old_departments = [
        'PSY BEH',
        'ENVIRON',
        'EHS',
        'BIOL',
        'PHMS',
    ]

    tree_parser = TreeParser('(', ')', ('and', 'or'))
    tokens = tree_parser.tokenize(string)

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

            if valid_courses is not None:
                split = token.split()
                department_code = ' '.join(split[:-1])
                course_number = split[-1]

                if department_code in department_remap:
                    #logger.info(f'Automatically remapped department code "{department_code}" to "{department_remap[department_code]}"')
                    department_code = department_remap[department_code]

                if department_code not in valid_courses:

                    if department_code in valid_but_old_departments:
                        pass  # ignore
                    else:
                        raise RuntimeError(f'Department code not found: "{department_code}"')

            stack[-1][1].append(token)

    if stack[-1][0] is None:
        stack[-1] = stack[-1][1][0]

    return stack[-1]


def parse_prerequisite_string(prerequisite_string: str) -> Union[str, List[List[str]]]:
    """
    Parse course prerequisites.
    :param prerequisite_string:
    :return: A tree of prerequisites represented as collection of nested lists. If there is only a single prerequisite,
    the returned value will be a string representing a course. If there are multiple prerequisites, the returned value
    will be a list of lists, each containing either a string representing a course, or another list. Each nested list
    has exactly 2 items. The first item is a string, either 'or' or 'and'. The second item is a list of courses.

    Examples:

    Prerequisite: "I&C SCI 45C"
    Return value: "I&C SCI 45C"

    Prerequisite: "(I&C SCI 46 or CSE 46) and I&C SCI 6D and (MATH 3A or I&C SCI 6N)"
    Return value: ['and', [['or', ['I&C SCI 46', 'CSE 46']], 'I&C SCI 6D', ['or', ['MATH 3A', 'I&C SCI 6N']]]]

    """

    # Split into sentences
    sentences = split_sentences(prerequisite_string)

    # Parse the first sentences. This contains the prerequisite courses.
    result = parse_prerequisite_courses(sentences[0])

    # TODO: Parse other statements (grade requirements, etc.)

    return result


def split_sentences(string):
    sentences = []
    sentence = ''
    found_space = False

    for c in string:

        # Ignore leading spaces
        if len(sentence) == 0 and c == ' ':
            continue

        if c == '.':
            if found_space:
                sentences.append(sentence)
                sentence = ''
                found_space = False
                continue
        if c == ' ':
            found_space = True

        sentence += c

    if len(sentence) > 0:
        sentences.append(sentence)

    return sentences


if __name__ == '__main__':
    parser = CatalogParser()
    courses = parser.get_courses()

    # Save to JSON
    with open('catalog.json', 'w') as file:
        json.dump(courses, file, indent=4)

    for c in courses:
        if 'prerequisite_or_corequisite' in c:
            print(c['prerequisite_or_corequisite'])
