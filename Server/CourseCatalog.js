
export class CourseCatalog
{
    constructor(mongoDbClient)
    {
        this.courses = []
        this.departments = []
        this.dbClient = mongoDbClient;
    }

    // Read all data from DB using mongodb client.
    LoadCatalog()
    {
        this.dbClient.retrieveDocument(this.SetCourses.bind(this));
    }

    SetCourses(courses)
    {
        this.courses = courses;
        console.log("number of courses : " +this.courses.length);
    }

    // Returns list of all departments.
    GetDepartments()
    {
        if(this.departments.length == 0)
        {
            this.courses.forEach((value,index,array) => {
                var depObj = {
                    deptId : value.deptId,
                    deptName : value.deptName
                }
                this.departments.push(depObj);
            });
        }
        return this.departments;
    }

    // Returns list of courses from department with name deptID.
    GetCourseList(deptId)
    {
        var courseList = this.courses.filter((value,index,array)=>{
            return value.deptId == deptId
        })
        console.log("Course list length :" + courseList.length);
        return courseList;
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
        this.dbClient.deleteAllDocuments();
    }
}