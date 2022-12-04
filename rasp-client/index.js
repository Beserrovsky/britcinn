const { MongoClient } = require('mongodb');
const mqtt = require('async-mqtt');

const express = require('express');
const bodyParser= require('body-parser');

const { Porcupine, BuiltinKeyword } = require("@picovoice/porcupine-node");
const { Rhino } = require("@picovoice/rhino-node");
const PvRecorder = require("@picovoice/pvrecorder-node");

// Picovoice stuff
const accessKey = ""

// Topic for db warnings
const WRN_TOPIC = 'BRITCINN_db';

// Database Name
const DB_NAME = 'BRITCINN';

// Database URI
const db_uri =
  'mongodb://127.0.0.1:27017/' + DB_NAME;

// Broker URI
const mqtt_uri = 
  'mqtt://broker.hivemq.com';

// Subscriptions
const SUBS = {'BRITCINN_ldr': {qos: 0}, 'BRITCINN_dht': {qos: 0}, 'BRITCINN_client': {qos: 0}};

async function db_conn() {
  try {
    await db_client.connect();

    let dbo = db_client.db(DB_NAME);

    dbo.command({ ping: 1 });

    console.log('Connected successfully to mongodb server!');
    
    return dbo;
  } finally { }
}

async function mqtt_conn() {
  try {
    client = await mqtt.connectAsync(mqtt_uri);
    
    console.log('Connected successfully to mqtt broker!');

    return client;
  } finally { }
}

async function handleMsg(topic, msg, dbo) {
  msg = msg.toString();

  console.log(`Message received on "${topic}": ${msg.toString()}`);

  try {
    let doc = JSON.parse(msg);
    doc.timestamp = Date.now();
    await saveDoc(doc, topic, dbo);
  } catch (e) {
    return console.error(e);
  }
}

const saveDoc = async (doc, collection, dbo) => {
  let col = dbo.collection(collection);
  const result = await col.insertOne(doc);
  console.log(
    `A ${collection} document was inserted with the _id: ${result.insertedId}`,
  );
}

const db_client = new MongoClient(db_uri);

async function main() {
  
  // Connect to MongoDB
  let dbo = await db_conn().catch(console.dir);

  // Connect to broker
  const client = await mqtt_conn().catch(console.dir);

  // Set cb
  await client.on('message', (topic, msg) => handleMsg(topic, msg, dbo));

  // Subscribes to topics
  await client.subscribe(SUBS, (err) => err? console.error : null);

  // Warning database recording
  await client.publish(WRN_TOPIC, 'Database recording started!');
  
  const app = express();

  app.use(bodyParser.urlencoded({ extended: true }));

  const server = app.listen(3000, function() {
    console.log('Express: listening on 3000')
  })

  for (const [key, value] of Object.entries(SUBS)) {
    console.log(`API endpoint created on: ${key}`);
    app.get(`/${key}`, async (req, res) => {
      let results = await dbo.collection(key).find().toArray();
      res.send(results);
    })
  }

  const porcupine = new Porcupine(
    accessKey,
    [BuiltinKeyword.PORCUPINE],
    [0.5]
  );

  const handle = new Rhino(accessKey, `${__dirname}/picovoice/context.rhn`);

  const recorder = new PvRecorder(-1, porcupine.frameLength);
  recorder.start();

  let running = true;

  // Defines exit routine
  process.on('SIGINT', async () => {

    // Closes conn to broker
    await client.end();
  
    // Closes conn to MongoDB
    await db_client.close();

    // Closes website
    server.close();
    
    console.log("\nTill next time, see ya!!!");
  });

  let index = -1;
  let isFinalized = false;

  while (running) {
    const frames = await recorder.read();

    if (index == -1) {
      index = porcupine.process(frames);
      if (index !== -1 ) { 
        console.log("Wake Word detected!"); 
        isFinalized = false;
      }
    } else {
      isFinalized = handle.process(frames);
      if (isFinalized) {
        const inference = handle.getInference();
        console.log(inference);
        index = -1;
        isFinalized = true;
      }
    }
  }
}

main();
