import { createRequire } from 'module';
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

    async removeDocuments()
    {
        try{
            await this.client.db(this.dbName).collection(this.collection).deleteMany({});
        }
        catch(error)
        {
            console.log(error);
        }
    }

    retrieveDocument(dbName = "CoursePlannerDB", collection = "Courses")
    {
        var db = this.client.db(dbName);
        var cursor = db.collection(collection).find();
        cursor.each(function(err, item) {
            // If the item is null then the cursor is exhausted/empty and closed
            if(item == null) {
                return;
            }

            console.log(item["courseName"]);
            // otherwise, do something with the item
        });
    }
}




