import Express from "express";
import {CourseCatalog} from './CourseCatalog.js';
import {MongoDbClient} from './MongoDbClient.js';
import fs from 'fs';

import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const {spawn} = require('child_process');

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

        res.setHeader('Content-Type', 'application/json');

        // Create new python process
        const python = spawn('python', ['../scheduler/create_schedule.py']);

        // Write data to STDIN
        python.stdin.write('{"a": 3}')
        python.stdin.end();

        // Read data from STDOUT
        let dataToSend;
        python.stdout.on('data', (data) => {
            console.log('Pipe data from python script ...');
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


