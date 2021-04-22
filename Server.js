import Express from "express";
import { MongoDbClient } from './DBReader.js';

class Routes
{
    courseData = [
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

// Uncomment to try out db connections
// let dbClient = new MongoDbClient();
// await dbClient.connect();
// await dbClient.listDatabases();
// await dbClient.close();

const app = Express();
const port = 3000;
let routes = new Routes();
app.get("/", routes.Root)
app.get("/course/:CourseID", routes.getcourseid);
app.listen(port, ()=> console.log("listening on port" + port ))


//app.post()
//app.delete()
