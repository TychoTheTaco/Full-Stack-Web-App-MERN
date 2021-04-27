export class Course 
{
    constructor(department_code, department_name, number, title, units)
    {
        this.courseId = "" + department_code + " " + number;
        this.deptId = department_code;
        this.deptName = department_name;
        this.courseName = title;
        this.units = units;
    }
}


// "department_code": "ANTHRO",
// "department_name": "Anthropology",
// "number": "125C",
// "title": "Environmental Anthropology",
// "units": "4",
// "description": "Introduces students to anthropological and qualitative research on the relationship of humans, non-humans, and environments. Focuses on how to analyze and evaluate social and cultural differences in environmental perception, relations, justice, governance, sustainability, and cosmology.",
// "prerequisite_courses": [
//     "or",
//     [
//         "ANTHRO 2A",
//         "ANTHRO 2B",
//         "ANTHRO 2C",
//         "ANTHRO 2D"
//     ]
// ],
// "ge_category": "III"