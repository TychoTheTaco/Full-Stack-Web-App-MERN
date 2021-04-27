
export class CourseCatalog
{
    constructor(mongoDbClient)
    {
        this.courses = []
        this.courseMap = new Map();
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
        this.courses.forEach((value,index,array) => {
        this.courseMap.set(value.courseId, value);
        });
    }

    // Returns list of all departments.
    GetDepartments()
    {
        if(this.departments.length == 0)
        {
            var prev = {
                deptId : "",
                deptName : ""
            };
            this.courses.forEach((value,index,array) => {
                var depObj = {
                    deptId : value.deptId,
                    deptName : value.deptName
                }
                if(prev["deptId"] != depObj["deptId"])
                this.departments.push(depObj);
                prev = depObj;
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
        this.SetDependencies(courseList);
        return courseList;
    }

    SetDependencies(courseList)
    {
        courseList.forEach((value,index,array) => {
        value["prereq"] = this.ReplacePreReq(value["prereq"])
        });
    }

    ReplacePreReq(prereq)
    {
        if(Array.isArray(prereq))
        {
            prereq.forEach((value,index,array)=>{
                console.log("Value : " + value)
                array[index] = this.ReplacePreReq(value);
            });
            return prereq;
        }
        
        if(this.courseMap.has(prereq))
        {
            prereq = this.courseMap.get(prereq);

            prereq["prereq"]= this.ReplacePreReq(prereq["prereq"]);
        }
        else
        {
            console.log("Course missing : " + prereq);
        }

        return prereq;
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