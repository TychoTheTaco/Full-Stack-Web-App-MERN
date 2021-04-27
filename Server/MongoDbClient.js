import { createRequire } from 'module';
import { Course } from "./Course.js";
const require = createRequire(import.meta.url);
const {MongoClient} = require('mongodb');

export class MongoDbClient {

    constructor(databseUri = "mongodb+srv://ObiWanCoursenobi:ObiWanCoursenobi@cluster0.hckjn.mongodb.net/CoursePlannerDB?retryWrites=true&w=majority",
    dbName = "CoursePlannerDB", collection = "Courses")
    {
        this.uri = databseUri;
        this.dbName = dbName;
        this.collection = collection;
        this.client = new MongoClient(this.uri, {
            useNewUrlParser: true,
            useUnifiedTopology: true,
        });
    }

    async connect() 
    {
        try 
        {
            await this.client.connect();
            console.log("Connected to mongodb");
        } 
        catch 
        {
            console.log("Failed to connect to mongodb");
        }
    }

    async close()
    {
        try{
            await this.client.close();
            console.log("Disconnected from mongodb");
        }
        catch{
            console.log("failed to disconnect");
        }
    }

    async insertDocument(docToInsert)
    {
        try{
            var db = this.client.db(this.dbName);
            await db.collection(this.collection).insertMany(docToInsert);
        }
        catch(error)
        {
            console.log(error);
        }

    }

    async deleteAllDocuments()
    {
        try{
            await this.client.db(this.dbName).collection(this.collection).deleteMany({});
        }
        catch(error)
        {
            console.log(error);
        }
    }

    retrieveDocument(callBack, dbName = "CoursePlannerDB", collection = "Courses")
    {
        let courses = []
        var db = this.client.db(dbName);
        var cursor = db.collection(collection).find();
        cursor.each(function(err, item) {
            if(item == null) {
                callBack(courses);
                return;
            }
            courses.push(new Course(item["department_code"], item["department_name"], item["number"],
                         item["title"], item["units"]));
        });
    }
}




