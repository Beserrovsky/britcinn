const { AudioBuffer } = require('web-audio-api')
const Microphone = require('node-microphone')

const { MongoClient } = require('mongodb');
const mqtt = require('async-mqtt');
const Picovoice = require("@picovoice/picovoice-node");
const express = require('express');
const bodyParser= require('body-parser');

// Picovoice stuff
const accessKey = "${ACCESS_KEY}"
const keywordArgument = "./key.ppn"
const contextPath = "./context.rhn"

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

// Picovoice

const keywordCallback = function (keyword) {
  console.log(`Wake word detected`);
};


const inferenceCallback = function (inference) {
  console.log("Inference:");
  console.log(JSON.stringify(inference, null, 4));
};

const picovoice = new Picovoice(
  accessKey,
  keywordArgument,
  keywordCallback,
  contextPath,
  inferenceCallback
);

function getNextAudioFrame() {
  // TODO: Get audio
  return audioFrame;
}

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

  app.listen(3000, function() {
    console.log('Express: listening on 3000')
  })

  for (const [key, value] of Object.entries(SUBS)) {
    console.log(`API endpoint created on: ${key}`);
    app.get(`/${key}`, async (req, res) => {
      let results = await db.collection(key).find().toArray();
      res.send(results);
    })
  }

  const rate = 44100
  const channels = 2 // Number of source channels

  const microphone = new Microphone({ // These parameters result to the arecord command above
    channels,
    rate,
    device: 'hw:1,0',
    bitwidth: 16,
    endian: 'little',
    encoding: 'signed-integer'
  })

  const audioBuffer = new AudioBuffer(
    1, // 1 channel
    30 * rate, // 30 seconds buffer
    rate
  )
  const chunks = []
  const data = audioBuffer.getChannelData(0) // This is the Float32Array
  const stream = microphone.startRecording()

  stream.on('data', chunk => {process.process(chunk);})

  // Defines exit routine
  process.on('SIGINT', async () => {

    // Closes conn to broker
    await client.end();
  
    // Closes conn to MongoDB
    await db_client.close();

    // Closes picovoice
    picovoice.release()

    // Stop microphone
    microphone.stopRecording()

    console.log("\nTill next time, see ya!!!");
  });
}

main();
