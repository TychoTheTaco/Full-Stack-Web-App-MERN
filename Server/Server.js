import Express from "express";
import {CourseCatalog} from './CourseCatalog.js';
import {MongoDbClient} from './MongoDbClient.js';
import fs from 'fs';

import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const {spawn} = require('child_process');

const url = require('url');

class Routes {
    constructor(catalog) {
        this.catalog = catalog
    }

    getDept = (req, res) => {
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify(this.catalog.GetDepartments(), null, 3));
    }

    getCourses = (req, res) => {

        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify(this.catalog.GetCourseList(req.params.deptId), null, 3));
    }

    getSchedule = (req, res) => {

        const queryParams = url.parse(req.url, true).query;

        /*
        Expected query params:
        required: a comma separated list of required courses.

        Example request:
        Courses: COMPSCI 111, COMPSCI 112, ART 11A
        http://localhost:5000/server/schedule?required=COMPSCI%20111%2C%20COMPSCI%20112%2C%20ART%2011A
         */

        // Required courses
        let requiredCourses = [];
        queryParams['required'].split(',').forEach(item => {
            requiredCourses.push(item.trim());
        })

        res.setHeader('Content-Type', 'application/json');

        // Create new python process
        const python = spawn('../venv/Scripts/python.exe', ['../scheduler/create_schedule.py']);

        const all_courses = catalog.GetRawData();

        const payload = {
            'catalog': all_courses,
            'required_courses': requiredCourses,
            'completed_courses': [],
            'max_courses_per_quarter': 4
        }

        // Write data to STDIN
        python.stdin.write(JSON.stringify(payload));
        python.stdin.end();

        // Read data from STDOUT
        let dataToSend;
        python.stdout.on('data', (data) => {
            dataToSend = data.toString();
        });

        // Send response when process has finished
        python.on('close', (code) => {
            console.log(`child process close all stdio with code ${code}`);
            res.end(dataToSend);
        });

    }
}

function resetDbFromFile(catalog, filePath = "./../catalog_parser/catalog.json") {
    fs.readFile(filePath, function (error, content) {
        if (error) {
            console.error(error);
            return;
        }
        catalog.clearCatalog();
        let data = JSON.parse(content);
        catalog.PutCourses(data);
    });
}

let mongoDbClient = new MongoDbClient();
let catalog = new CourseCatalog(mongoDbClient);

mongoDbClient.connect().then((resetDb = false) => {
    if (resetDb == true) {
        resetDbFromFile(catalog);
    }
    catalog.LoadCatalog();
    app.emit('ready');
});

const app = Express();
const port = 5000;
let routes = new Routes(catalog);
app.get("/server/departments", routes.getDept);
app.get("/server/departments/:deptId/courses", routes.getCourses);
app.get("/server/schedule", routes.getSchedule);

app.on('ready', function () {
    app.listen(port, () => console.log("listening on port" + port));
}); 


