export class CourseCatalog
{
    constructor(mongoDbClient)
    {
        this.deptIds = new Set();
        this.courses = []
        this.courseMap = new Map();
        this.deptCourses = new Map();
        this.departments = []
        this.dbClient = mongoDbClient;
        this.rawData = [];
    }

    // Read all data from DB using mongodb client.
    LoadCatalog() {
        this.dbClient.retrieveDocument(this.SetCourses.bind(this));
        this.dbClient.getRawData((data) => {
            this.rawData = data;
        });
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
            this.courses.forEach((value,index,array) => {
                
                if(!this.deptIds.has(value.deptId))
                {
                    var depObj = {
                        deptId : value.deptId,
                        deptName : value.deptName
                    }
                    this.departments.push(depObj);
                    this.deptIds.add(value.deptId);
                }
            });
        }
        return this.departments;
    }

    GetRawData() {
        return this.rawData;
    }

    // Returns list of courses from department with name deptID.
    GetCourseList(deptId)
    {
        if(this.deptCourses.has(deptId))
        {
            return this.deptCourses.get(deptId);
        }
        var courseList = this.courses.filter((value,index,array)=>{
            return value.deptId == deptId
        })
        console.log("Course list length :" + courseList.length);
        this.SetDependencies(courseList);
        this.deptCourses.set(deptId,courseList);
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