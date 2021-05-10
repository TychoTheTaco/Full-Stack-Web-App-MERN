import sys
import json
import traceback

import scheduler


def main():
    std_input = sys.stdin.read()
    input_json = json.loads(std_input)

    course_catalog = input_json['catalog']
    required_courses = input_json['required_courses']
    completed_courses = input_json['completed_courses']
    max_courses_per_quarter = input_json['max_courses_per_quarter']

    schedule = scheduler.create_schedule(
        course_catalog,
        required_courses,
        max_courses_per_quarter=max_courses_per_quarter,
        completed_courses=completed_courses
    )

    print(schedule)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
