import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const {MongoClient} = require('mongodb');

export class MongoDbClient {

    constructor(databseUri = "mongodb+srv://ObiWanCoursenobi:ObiWanCoursenobi@cluster0.hckjn.mongodb.net/CoursePlannerDB?retryWrites=true&w=majority")
    {
        this.uri = databseUri;
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

    async listDatabases()
    {
        var databasesList = await this.client.db().admin().listDatabases();
        console.log("Databases:");
        databasesList.databases.forEach(db => console.log(` - ${db.name}`));
    }

    async insertDocument()
    {

    }

    async retrieveDocument()
    {

    }
}




