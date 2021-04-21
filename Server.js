import Express from "express";
//import CourseData from "./CourseData.js";
import { MongoDbClient } from './DBReader.js';

let dbClient = new MongoDbClient();
await dbClient.connect();
await dbClient.listDatabases();
await dbClient.close();

const app = Express();
const port = 3000;
const CourseData = [
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

app.get("/", (req,res)=> {
    res.json(CourseData)
})


app.get("/course/:CourseID", (req,res)=> {
    res.json(CourseData.find((course)=>{
        return req.params.CourseID === course.CourseID
    }))
    
})

//app.listen(port, ()=> console.log("listening on port" + port ))
//app.post()
//app.delete()
