import Express from "express";
import { CourseCatalog } from './CourseCatalog.js';
import { MongoDbClient } from './MongoDbClient.js';
import fs from 'fs';

class Routes
{
    constructor()
    {

    }

    Root = (req, res) => {
        res.send("Welcome obi wan coursenobi.");
    }

    getDept = (req,res) => {
        res.send("list of departments.");
    }

    getCourses = (req,res) => {
        console.log("getcourses for department " + req.params.deptId);
        res.send("list of courses in department " + req.params.deptId);
    }

    getcourseid = (req,res)=> {
        res.json(this.courseData.find((course)=>{
            return req.params.CourseID === course.CourseID
        }))  
    }

}

function resetDbFromFile(catalog, filePath = "./../catalog_parser/catalog.json") {
    fs.readFile(filePath, function (error, content) {
        if(error)
        {
            console.error(error);
            return;
        }
        catalog.clearCatalog();
        let data = JSON.parse(content);
        catalog.PutCourses(data);
    });
}

let mongoDbClient = new MongoDbClient();
mongoDbClient.connect().then((resetDb = false)=>
{
    let catalog = new CourseCatalog(mongoDbClient);

    if(resetDb == true)
    {
        resetDbFromFile(catalog);
    }

    app.emit('ready');
});

const app = Express();
const port = 3000;
let routes = new Routes();
app.get("/coursenobi/departments", routes.getDept);
app.get("/coursenobi/departments/:deptId/courses", routes.getCourses);

app.on('ready', function() { 
    app.listen(port, ()=> console.log("listening on port" + port));
}); 


