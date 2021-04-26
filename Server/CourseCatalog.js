
export class CourseCatalog
{
    constructor(mongoDbClient)
    {
        this.dbClient = mongoDbClient;
    }

    // Read all data from DB using mongodb client.
    LoadCatalog()
    {

    }

    // Returns list of all departments.
    GetDepartments()
    {

    }

    // Returns list of courses from department with name deptName.
    GetCourseList(deptName)
    {

    }

    // Returns a tree of courses and their prerequisites
    GetCourseGraph(deptName)
    {

    }

    // Returns true on successful commit of 'courses' to mongodb.
    // courses : JSON array of courses.
    PutCourses(courses)
    {
        this.dbClient.insertDocument(courses);
    }

    clearCatalog()
    {
        this.dbClient.removeDocuments();
    }
}