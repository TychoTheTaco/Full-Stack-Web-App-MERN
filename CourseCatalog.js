import { MongoDbClient } from './MongoDbClient.js';

export class CourseCatalog
{
    constructor()
    {
        this.dbClient = new MongoDbClient();
    }

    // Read all data from DB using mongodb client.
    async LoadCatalog()
    {
        await this.dbClient.connect().then(res =>{ 
            console.log("IsConnected");
            this.dbClient.retrieveDocument();
        });
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

    // Call to close db connectivity.
    CloseCatalog()
    {
        this.dbClient.close();
    }
}