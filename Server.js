import Express from "express";
import { CourseCatalog } from './CourseCatalog.js';


const courseData = [
    {
        "CourseID" : "A",
        "CourseName" : "courseA",
        "Prerequisites" : ["B", "C"]
    },
    {
        "CourseID" : "B",
        "CourseName" : "courseB",
        "Prerequisites" : []
    },
    {
        "CourseID" : "C",
        "CourseName" : "courseC",
        "Prerequisites" : []
    }
];

class Routes
{
    constructor()
    {

    }

    Root = (req, res) => {
        res.json(this.courseData);
    }

    getcourseid = (req,res)=> {
        res.json(this.courseData.find((course)=>{
            return req.params.CourseID === course.CourseID
        }))  
    }

}


let catalog = new CourseCatalog();
catalog.LoadCatalog().then(catalog.PutCourses(courseData));

/// Uncomment to publish server.
// const app = Express();
// const port = 3000;
// let routes = new Routes();
// app.get("/", routes.Root)
// app.get("/course/:CourseID", routes.getcourseid);
// app.post()
// app.delete()
// app.listen(port, ()=> console.log("listening on port" + port ))



